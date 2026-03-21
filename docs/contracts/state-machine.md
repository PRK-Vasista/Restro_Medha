# State Machines (MVP)

## Order State

`placed -> in_prep -> ready -> served`

Allowed cancellation:

- `placed -> cancelled`
- `in_prep -> cancelled` (requires manager role)

Forbidden transitions are rejected with HTTP 409.

## Bill State

`draft -> finalized -> paid`

`finalized` is immutable. Any correction requires:

1. Manager-authorized void (`void_reason` mandatory)
2. New bill referencing `supersedes_bill_id`

## KOT State

`queued -> acknowledged -> preparing -> complete`

KOT state updates are idempotent by `(ticket_id, desired_state, actor_id)` key.
