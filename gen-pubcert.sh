#!/bin/sh
set -eu
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 private-key certificate subject" >&2
    exit 2
fi
KEY=$1
CERT=$2
SUBJECT=$3
umask 077
openssl req -new -x509 -sha256 -key "$KEY" -out "$CERT" -days 3650 -subj "/CN=$SUBJECT" >/dev/null 2>&1
