"""
File: entities.py
Purpose: Pure domain data carriers (entities and value objects).
Responsibilities: Hold typed fields only; no persistence or HTTP knowledge.

Note: These mirror persisted shapes loosely; serialization happens in infrastructure layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from restro_billing.core.domain.enums import BillState, KotState, OrderState


@dataclass(frozen=True)
class OrderLine:
    """
    Class: OrderLine
    Description: Single sellable line on an order (value object).

    Attributes:
        item_id: Menu SKU identifier.
        item_name: Display name at time of order.
        qty: Quantity ordered.
        unit_price: Unit price snapshot.

    Example usage:
        OrderLine("it-1", "Dosa", 2, 120.0)
    """

    item_id: str
    item_name: str
    qty: float
    unit_price: float


@dataclass
class Order:
    """
    Class: Order
    Description: Table order aggregate root identifier + state (minimal projection).

    Attributes:
        id: UUID string.
        tenant_id: SaaS tenant scope.
        table_no: Optional floor table label.
        state: Current OrderState.
        lines: Parsed line items.
        created_at: ISO timestamp.

    Example usage:
        Order(id="...", tenant_id="default", table_no="T1", state=OrderState.placed, lines=[], created_at="...")
    """

    id: str
    tenant_id: str
    table_no: str | None
    state: OrderState
    lines: list[OrderLine]
    created_at: str


@dataclass
class KotTicket:
    """
    Class: KotTicket
    Description: Kitchen ticket projection.

    Attributes:
        id, tenant_id, order_id, state, created_at.

    Example usage:
        KotTicket(...)
    """

    id: str
    tenant_id: str
    order_id: str
    state: KotState
    created_at: str


@dataclass
class Bill:
    """
    Class: Bill
    Description: Invoice aggregate summary.

    Attributes:
        id, tenant_id, order_id, state, subtotal, tax_total, grand_total, gstin, payload, created_at.

    Example usage:
        Bill(...)
    """

    id: str
    tenant_id: str
    order_id: str
    state: BillState
    subtotal: float
    tax_total: float
    grand_total: float
    gstin: str | None
    payload: dict[str, Any]
    created_at: str


@dataclass
class MenuItem:
    """
    Class: MenuItem
    Description: Catalog row for GST-ready menu.

    Attributes:
        item_id, tenant_id, name, category, hsn_code, unit_price, updated_at.

    Example usage:
        MenuItem(...)
    """

    item_id: str
    tenant_id: str
    name: str
    category: str
    hsn_code: str
    unit_price: float
    updated_at: str


@dataclass
class LedgerEvent:
    """
    Class: LedgerEvent
    Description: Append-only ledger row (audit).

    Attributes:
        event_id, tenant_id, event_type, entity_type, entity_id, payload, checksum, created_at.

    Example usage:
        LedgerEvent(...)
    """

    event_id: str
    tenant_id: str
    event_type: str
    entity_type: str
    entity_id: str
    payload: dict[str, Any]
    checksum: str
    created_at: str


@dataclass
class RevenueReport:
    """
    Class: RevenueReport
    Description: Read-model for analytics (not persisted as entity).

    Attributes:
        total_bills, gross_revenue, top_selling_items.

    Example usage:
        RevenueReport(1, 100.0, [])
    """

    total_bills: int
    gross_revenue: float
    top_selling_items: list[dict[str, Any]] = field(default_factory=list)
