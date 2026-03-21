#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"

healthcheck() {
  curl -sf "$BASE_URL/health" >/dev/null
}

create_order_and_bill() {
  ORDER_JSON=$(curl -sS -X POST "$BASE_URL/orders" \
    -H "Content-Type: application/json" \
    -H "X-Role: cashier" \
    -H "Idempotency-Key: test-order-1" \
    -d '{"table_no":"T10","lines":[{"item_id":"it-1","item_name":"Dosa","qty":2,"unit_price":120}]}' )

  ORDER_ID=$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["order_id"])' <<< "$ORDER_JSON")

  curl -sS -X POST "$BASE_URL/bills" \
    -H "Content-Type: application/json" \
    -H "X-Role: cashier" \
    -H "Idempotency-Key: test-bill-1" \
    -d "{\"order_id\":\"$ORDER_ID\",\"gstin\":\"27ABCDE1234F1Z5\"}" >/dev/null
}

sync_replay() {
  curl -sS -X POST "$BASE_URL/sync/events" \
    -H "Content-Type: application/json" \
    -H "X-Role: kitchen_staff" \
    -d '{"message_id":"msg-1","source_device_id":"test-kds","sequence":1,"sent_at":"2026-01-01T00:00:00Z","payload":{"status":"queued"}}' >/dev/null
  REPLAY=$(curl -sS "$BASE_URL/sync/replay" -H "X-Role: kitchen_staff")
  python3 -c 'import json,sys; data=json.loads(sys.stdin.read()); assert any(item.get("MessageID")=="msg-1" or item.get("message_id")=="msg-1" for item in data)' <<< "$REPLAY"
}

healthcheck
create_order_and_bill
sync_replay

echo "Resilience smoke tests passed"
