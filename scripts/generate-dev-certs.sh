#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-infra/certs}"
mkdir -p "$OUT_DIR"

openssl genrsa -out "$OUT_DIR/ca.key" 2048
openssl req -x509 -new -nodes -key "$OUT_DIR/ca.key" -sha256 -days 365 -subj "/CN=RestroMedhaCA" -out "$OUT_DIR/ca.crt"

openssl genrsa -out "$OUT_DIR/server.key" 2048
openssl req -new -key "$OUT_DIR/server.key" -subj "/CN=gateway" -out "$OUT_DIR/server.csr"
openssl x509 -req -in "$OUT_DIR/server.csr" -CA "$OUT_DIR/ca.crt" -CAkey "$OUT_DIR/ca.key" -CAcreateserial -out "$OUT_DIR/server.crt" -days 365 -sha256

openssl genrsa -out "$OUT_DIR/client.key" 2048
openssl req -new -key "$OUT_DIR/client.key" -subj "/CN=pos-client" -out "$OUT_DIR/client.csr"
openssl x509 -req -in "$OUT_DIR/client.csr" -CA "$OUT_DIR/ca.crt" -CAkey "$OUT_DIR/ca.key" -CAcreateserial -out "$OUT_DIR/client.crt" -days 365 -sha256

echo "Certificates generated in $OUT_DIR"
