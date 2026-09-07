#!/bin/sh
set -eu

UPSTREAM_BASE=${UPSTREAM_BASE:-https://raw.githubusercontent.com/sforshee/wireless-regdb/master}
DB_SHA1=16b38b7cb2b21ff196654ccad80b98337af93316
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fetch() {
    curl --fail --location --silent --show-error --proto '=https' --tlsv1.2 "$UPSTREAM_BASE/$1" -o "$TMP/$1"
}

fetch db.txt
fetch dbparse.py

printf '%s  %s\n' "$DB_SHA1" "$TMP/db.txt" | sha1sum -c -
install -m 0644 "$TMP/db.txt" db.txt
install -m 0755 "$TMP/dbparse.py" dbparse.py
printf '%s  db.txt\n' "$DB_SHA1" > sha1sum.txt
printf '%s\n' "Synchronized db.txt and dbparse.py from $UPSTREAM_BASE"
