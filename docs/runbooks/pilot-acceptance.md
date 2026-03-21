# Pilot Acceptance Gates

## Functional
- RBAC checks pass for manager/cashier/kitchen_staff.
- Billing + GST invoice generation verified with mandatory fields.
- KDS state lifecycle completes for live orders.
- Menu bulk import and category filtering pass.
- Revenue and top-selling reports return expected values.

## Resilience
- Order-to-bill works during internet disconnect.
- Sync replay after reconnect creates no duplicates.
- Backup and restore scripts complete successfully.

## Operational
- CI pipeline green on default branch.
- Rollback drill completed with documented outcome.
- On-site support contact matrix and SOP shared with pilot outlet.
