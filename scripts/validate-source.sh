#!/bin/sh
set -eu
[ -s db.txt ]
grep -q '^country 00:' db.txt
grep -q '^country NG:' db.txt
grep -q '^country US:' db.txt
sha1sum -c sha1sum.txt
printf '%s\n' 'wireless-regdb source validation passed'
