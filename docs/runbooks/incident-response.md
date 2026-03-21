# Incident Response Runbook

## Router/Internet outage
- Confirm gateway reachable from LAN.
- Continue operations in offline mode.
- Verify sync queue growth and no billing interruption.

## Edge power failure
- Bring edge server back online.
- Validate ledger integrity via `/ledger/events`.
- Reconcile last printed invoice with ledger and reissue only via void/recreate workflow.

## Certificate expiry risk
- Rotate certs 7 days before expiry.
- Restart gateway with updated files.
- Validate mTLS handshake from POS client.
