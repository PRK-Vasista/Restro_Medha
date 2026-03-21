#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${1:-./data}"
OUT_DIR="${2:-./backups}"
PASSPHRASE="${BACKUP_PASSPHRASE:-}"

if [[ -z "$PASSPHRASE" ]]; then
  echo "BACKUP_PASSPHRASE is required" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
TS="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="$OUT_DIR/restro-edge-$TS.tar.gz"
ENCRYPTED="$ARCHIVE.enc"

tar -czf "$ARCHIVE" -C "$DATA_DIR" .
openssl enc -aes-256-cbc -pbkdf2 -salt -in "$ARCHIVE" -out "$ENCRYPTED" -pass env:BACKUP_PASSPHRASE
rm -f "$ARCHIVE"

echo "$ENCRYPTED"
