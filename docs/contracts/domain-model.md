# Domain Model (MVP)

## Canonical Entities

- `User`: authenticated actor with role.
- `Role`: `manager`, `cashier`, `kitchen_staff`.
- `Table`: dine-in seating assignment.
- `MenuItem`: sellable SKU with tax metadata.
- `Order`: collection of order lines with lifecycle state.
- `OrderLine`: line-level quantity, price, and notes.
- `KOTTicket`: kitchen work item derived from order state.
- `Bill`: immutable financial settlement record.
- `Payment`: payment event linked to bill.
- `RecipeMap`: ingredient mapping per menu item.
- `StockAdjustment`: additive inventory event with reason.
- `LedgerEvent`: append-only event for durability and replay.

## Identifiers

All entities use UUIDv7 IDs to preserve temporal ordering in distributed systems.

## Timestamps

All timestamps are UTC RFC3339 with milliseconds.

## Invariants

- Finalized bills cannot be mutated.
- Corrections are modeled as `void + reissue` chain.
- Inventory is event-sourced; no destructive rewrites.
- Order state transitions are monotonic.
