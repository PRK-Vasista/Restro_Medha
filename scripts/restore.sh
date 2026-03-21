#!/usr/bin/env bash
set -euo pipefail

ENCRYPTED_FILE="${1:-}"
TARGET_DIR="${2:-./data}"
PASSPHRASE="${BACKUP_PASSPHRASE:-}"

if [[ -z "$ENCRYPTED_FILE" ]]; then
  echo "Usage: restore.sh <encrypted-backup-file> [target-dir]" >&2
  exit 1
fi
if [[ -z "$PASSPHRASE" ]]; then
  echo "BACKUP_PASSPHRASE is required" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"
TMP_ARCHIVE="/tmp/restro-restore-$$.tar.gz"
openssl enc -d -aes-256-cbc -pbkdf2 -in "$ENCRYPTED_FILE" -out "$TMP_ARCHIVE" -pass env:BACKUP_PASSPHRASE
tar -xzf "$TMP_ARCHIVE" -C "$TARGET_DIR"
rm -f "$TMP_ARCHIVE"

echo "Restored into $TARGET_DIR"
