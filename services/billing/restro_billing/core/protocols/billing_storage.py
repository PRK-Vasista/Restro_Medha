"""
File: billing_storage.py
Purpose: Abstract persistence port for the billing bounded context.
Responsibilities: Define interfaces implemented by SQLite (or future Postgres) adapters.

Classes here are Protocols — no implementation, enables DI and testing with fakes.
"""

from __future__ import annotations

from typing import Any, Protocol


class BillingStoragePort(Protocol):
    """
    Class: BillingStoragePort
    Description: Port interface for all persistence operations used by application services.

    Attributes:
        None (protocol).

    Example usage:
        def __init__(self, storage: BillingStoragePort): ...
    """

    def migrate(self) -> None:
        """Run schema migrations / ensure columns."""
        ...

    def get_idempotent_response(self, tenant_id: str, key: str, endpoint: str) -> dict[str, Any] | None:
        """Return cached JSON response if idempotency key hit."""
        ...

    def save_idempotent_response(self, tenant_id: str, key: str, endpoint: str, response: dict[str, Any]) -> None:
        """Persist idempotency mapping."""
        ...

    def create_order_with_kot(
        self,
        tenant_id: str,
        order_id: str,
        table_no: str | None,
        lines_payload: dict[str, Any],
        kot_id: str,
        created_at: str,
    ) -> None:
        """Insert order row + KOT + ledger events."""
        ...

    def get_order_row(self, tenant_id: str, order_id: str) -> dict[str, Any] | None:
        """Return {state, payload} or None."""
        ...

    def update_order_state(self, tenant_id: str, order_id: str, new_state: str, ledger_payload: dict[str, Any]) -> None:
        """Update order state and append ledger."""
        ...

    def insert_bill(
        self,
        tenant_id: str,
        bill_id: str,
        order_id: str,
        state: str,
        subtotal: float,
        tax_total: float,
        grand_total: float,
        gstin: str | None,
        payload: dict[str, Any],
        created_at: str,
        ledger_payload: dict[str, Any],
    ) -> None:
        """Persist finalized bill + ledger."""
        ...

    def upsert_menu_items(self, tenant_id: str, items: list[dict[str, Any]], updated_at: str) -> int:
        """Bulk upsert menu; returns count."""
        ...

    def list_menu_items(self, tenant_id: str, category: str | None) -> list[dict[str, Any]]:
        """List catalog rows."""
        ...

    def list_kot_tickets(self, tenant_id: str, limit: int) -> list[dict[str, Any]]:
        """List KOT rows newest first."""
        ...

    def get_kot_row(self, tenant_id: str, ticket_id: str) -> dict[str, Any] | None:
        """Return {order_id, state} or None."""
        ...

    def update_kot_state(self, tenant_id: str, ticket_id: str, new_state: str, ledger_payload: dict[str, Any]) -> None:
        """Update KOT + ledger."""
        ...

    def revenue_aggregates(self, tenant_id: str) -> tuple[int, float, list[dict[str, Any]]]:
        """Returns (total_bills, gross_revenue, top_items)."""
        ...

    def list_ledger_events(self, tenant_id: str, limit: int) -> list[dict[str, Any]]:
        """Recent ledger rows."""
        ...
