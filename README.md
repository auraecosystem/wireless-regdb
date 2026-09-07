# wireless-regdb

This repository contains the wireless regulatory database build and packaging infrastructure.

The authoritative regulatory source is `db.txt`. The build tools convert it into the legacy `regulatory.bin` format and the modern `regulatory.db` format. `regulatory.db.p7s` is an OpenSSL CMS/PKCS#7 signature over `regulatory.db`.

## Build

The build requires Python 3, OpenSSL, GNU make, and the dependencies needed by `db2bin.py` when generating a signed `regulatory.bin`.

```sh
./scripts/sync-upstream-db.sh
make
```

Private signing keys are generated locally under the user's home directory and are never intended to be committed to Git.

## Regulatory data provenance

`db.txt` must be sourced from the upstream wireless-regdb project or an explicitly approved Debian source snapshot. Do not hand-edit regulatory limits without authoritative evidence.

The synchronization helper pins the upstream source by SHA-1 and refuses an unexpected source, providing a reproducible guard against accidental substitution.

## Outputs

- `regulatory.bin` — legacy signed regulatory database.
- `regulatory.db` — current binary regulatory database.
- `regulatory.db.p7s` — detached CMS signature.
- `sha1sum.txt` — source integrity record for `db.txt`.

## Security

Do not commit private keys, generated certificates containing private material, or distribution signing credentials. CI should use ephemeral test keys unless production signing credentials are supplied through a protected secret mechanism.

## Upstream

Upstream project: https://github.com/sforshee/wireless-regdb
