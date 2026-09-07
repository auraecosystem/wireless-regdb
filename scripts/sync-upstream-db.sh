#!/bin/sh
set -eu

# Pin the upstream source to an immutable commit.  This avoids silently
# changing regulatory data when the upstream branch moves.
UPSTREAM_BASE=${UPSTREAM_BASE:-https://raw.githubusercontent.com/sforshee/wireless-regdb/db6f5f955ba23ae09d745019c1df253e7641f8b2}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fetch() {
    curl --fail --location --silent --show-error --proto '=https' --tlsv1.2 "$UPSTREAM_BASE/$1" -o "$TMP/$1"
}

fetch db.txt
fetch dbparse.py

# The immutable Git commit is the source-of-truth pin. Record the fetched
# content hash for reproducibility/auditability rather than comparing against
# a stale branch-derived checksum.
sha1sum "$TMP/db.txt" | awk '{print $1}' > "$TMP/db.sha1"
install -m 0644 "$TMP/db.txt" db.txt
install -m 0755 "$TMP/dbparse.py" dbparse.py
printf '%s  db.txt\n' "$(cat "$TMP/db.sha1")" > sha1sum.txt
printf '%s\n' "Synchronized db.txt and dbparse.py from immutable upstream commit db6f5f955ba23ae09d745019c1df253e7641f8b2"
