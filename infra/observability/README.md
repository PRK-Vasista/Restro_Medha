# Observability Baseline

MVP observability standard:

- Structured JSON logs from each service.
- Edge local log retention minimum 7 days.
- Health endpoints monitored every 30s:
  - `/health` on gateway/billing/inventory/sync
- Alert conditions:
  - Service unavailable for > 2 minutes.
  - Billing create operation p95 > 300ms over 5 minutes.
  - Sync replay lag (oldest queued event) > 10 minutes.

## Suggested collector

Use any edge-compatible log collector (Vector/Fluent Bit) and forward to cloud hub only when online.
