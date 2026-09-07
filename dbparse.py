#!/usr/bin/env python3
"""Parser for the wireless-regdb db.txt format."""
from functools import total_ordering
import math
import sys

FLAG_DEFINITIONS = {
    'NO-OFDM': 1 << 0, 'NO-CCK': 1 << 1, 'NO-INDOOR': 1 << 2,
    'NO-OUTDOOR': 1 << 3, 'DFS': 1 << 4, 'PTP-ONLY': 1 << 5,
    'PTMP-ONLY': 1 << 6, 'NO-IR': 1 << 7, 'NO-HT40': 1 << 10,
    'AUTO-BW': 1 << 11,
}
DFS_REGIONS = {'DFS-FCC': 1, 'DFS-ETSI': 2, 'DFS-JP': 3}

@total_ordering
class WmmRule:
    def __init__(self, vo_c, vi_c, be_c, bk_c, vo_ap, vi_ap, be_ap, bk_ap):
        self.values = (vo_c, vi_c, be_c, bk_c, vo_ap, vi_ap, be_ap, bk_ap)
    def _as_tuple(self): return self.values
    def __eq__(self, other): return other is not None and self.values == other.values
    def __lt__(self, other): return other is not None and self.values < other.values
    def __hash__(self): return hash(self.values)

@total_ordering
class FreqBand:
    def __init__(self, start, end, bw, comments=None): self.start, self.end, self.maxbw, self.comments = start, end, bw, comments or []
    def _as_tuple(self): return (self.start, self.end, self.maxbw)
    def __eq__(self, other): return self._as_tuple() == other._as_tuple()
    def __lt__(self, other): return self._as_tuple() < other._as_tuple()
    def __hash__(self): return hash(self._as_tuple())
    def __str__(self): return '<FreqBand %.3f - %.3f @ %.3f>' % self._as_tuple()

@total_ordering
class PowerRestriction:
    def __init__(self, max_ant_gain, max_eirp, comments=None): self.max_ant_gain, self.max_eirp, self.comments = max_ant_gain, max_eirp, comments or []
    def _as_tuple(self): return (self.max_ant_gain, self.max_eirp)
    def __eq__(self, other): return self._as_tuple() == other._as_tuple()
    def __lt__(self, other): return self._as_tuple() < other._as_tuple()
    def __hash__(self): return hash(self._as_tuple())

@total_ordering
class Permission:
    def __init__(self, freqband, power, flags, wmmrule=None):
        self.freqband, self.power, self.wmmrule = freqband, power, wmmrule
        self.textflags = tuple(flags); self.flags = 0
        for flag in flags:
            if flag not in FLAG_DEFINITIONS: raise ValueError('Unknown flag %s' % flag)
            self.flags |= FLAG_DEFINITIONS[flag]
    def _as_tuple(self): return (self.freqband, self.power, self.flags, self.wmmrule)
    def __eq__(self, other): return self._as_tuple() == other._as_tuple()
    def __lt__(self, other): return self._as_tuple() < other._as_tuple()
    def __hash__(self): return hash(self._as_tuple())

class Country:
    def __init__(self, dfs_region, permissions=None, comments=None):
        self._permissions = list(permissions or []); self.comments = comments or []
        self.dfs_region = DFS_REGIONS.get(dfs_region, 0) if dfs_region else 0
        if dfs_region and dfs_region not in DFS_REGIONS: raise ValueError('Unknown DFS region %s' % dfs_region)
    def add(self, perm): self._permissions.append(perm); self._permissions.sort()
    def __contains__(self, perm): return perm in self._permissions
    @property
    def permissions(self): return tuple(self._permissions)

class SyntaxError(Exception): pass
class DFSRegionError(Exception): pass
class FlagError(Exception): pass

class DBParser:
    def __init__(self, warn=None): self.warn = warn or sys.stderr.write
    def _error(self, line, msg): raise SyntaxError('Syntax error in line %d (%s)' % (line, msg))
    def _power(self, value, line):
        value = value.strip()
        if value == 'N/A': return 0.0
        try:
            if value.endswith('mW'): return 10.0 * math.log10(float(value[:-2]))
            return float(value)
        except ValueError: self._error(line, 'invalid power data')
    def _band(self, spec, line):
        try: freqs, bw = spec.split('@', 1); start, end = [float(x.strip()) for x in freqs.split('-', 1)]
        except (ValueError, TypeError): self._error(line, 'band must have frequency range')
        bw = float(bw.strip() or 20.0)
        if start <= 0 or end <= 0 or start >= end: self._error(line, 'invalid frequency range')
        return FreqBand(start, end, bw)
    def parse(self, fp):
        bands, powers, countries, wmm = {}, {}, {}, {}
        current = None; comments = []; current_wmm = None
        for lineno, raw in enumerate(fp, 1):
            line = raw.rstrip('\n'); stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('#'):
                comments.append(stripped); continue
            if stripped.startswith('wmmrule '):
                current_wmm = stripped.split(None, 1)[1].rstrip(':').strip(); wmm[current_wmm] = {}; continue
            if current_wmm and line[:1].isspace() and ':' in stripped and not stripped.startswith(('country ', 'band ', 'power ')):
                ac, vals = stripped.split(':', 1); fields = {}
                for item in vals.split(','):
                    k, v = item.strip().split('=', 1); fields[k] = int(v)
                wmm[current_wmm][ac.strip()] = (fields['cw_min'], fields['cw_max'], fields['aifsn'], fields['cot']); continue
            if stripped.startswith('band '):
                current_wmm = None; name, spec = stripped[5:].split(':', 1); bands[name.strip()] = self._band(spec.strip(), lineno); continue
            if stripped.startswith('power '):
                current_wmm = None; name, spec = stripped[6:].split(':', 1); powers[name.strip()] = PowerRestriction(0.0, self._power(spec, lineno)); continue
            if stripped.startswith('country '):
                current_wmm = None; head, rest = stripped[8:].split(':', 1); dfs = rest.strip()
                for name in head.split(','):
                    countries[name.strip().encode('ascii')] = Country(dfs, comments=comments); current = countries[name.strip().encode('ascii')]
                comments = []; continue
            if current is None: self._error(lineno, 'data outside country')
            if not line[:1].isspace(): self._error(lineno, 'country definition must be indented')
            parts = [p.strip() for p in stripped.split(',')]
            if parts[0].startswith('('):
                try: band_spec, power_part = stripped.split('),', 1); band_spec = band_spec[1:]; band = self._band(band_spec, lineno)
                except ValueError: self._error(lineno, 'badly parenthesised band definition')
                power_part = power_part.strip(); parts = [power_part]
            else:
                name = parts.pop(0); band = bands.get(name)
                if band is None: self._error(lineno, 'band does not exist')
            if not parts: self._error(lineno, 'country definition must have power')
            ppart = parts.pop(0)
            if ppart.startswith('('):
                if not ppart.endswith(')'): self._error(lineno, 'badly parenthesised power definition')
                power = PowerRestriction(0.0, self._power(ppart[1:-1], lineno))
            else:
                power = powers.get(ppart)
                if power is None: self._error(lineno, 'power does not exist')
            flags = [x.strip() for x in parts if x.strip()]
            wmmrule = None
            for flag in list(flags):
                if flag.startswith('wmmrule='):
                    flags.remove(flag); name = flag.split('=', 1)[1]
                    data = wmm.get(name)
                    if data is None: self._error(lineno, 'no wmm rule for %s' % name)
                    vals = [data[k] for k in ('vo_c','vi_c','be_c','bk_c','vo_ap','vi_ap','be_ap','bk_ap')]
                    wmmrule = WmmRule(*sum((list(v) for v in vals), []))
            try: current.add(Permission(band, power, flags, wmmrule))
            except ValueError as exc: self._error(lineno, str(exc))
        return countries
