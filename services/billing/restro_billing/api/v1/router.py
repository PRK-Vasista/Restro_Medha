"""
File: router.py
Purpose: Versioned REST controllers (API layer only).
Responsibilities: Map HTTP to application services; validate input; no business rules.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header

from restro_billing.api.deps import (
    get_billing_application_service,
    get_effective_tenant_id,
    get_kds_service,
    get_ledger_service,
    get_menu_service,
    get_order_service,
    get_revenue_service,
    require_roles,
)
from restro_billing.api.v1.schemas import (
    BulkMenuImportBody,
    CreateBillBody,
    CreateOrderBody,
    KdsStateBody,
    OrderStatePatchBody,
)
from restro_observability import get_logger
from restro_billing.features.billing_flow.application.billing_service import BillingApplicationService
from restro_billing.features.kitchen_display.application.kds_service import KdsService
from restro_billing.features.ledger.application.ledger_service import LedgerQueryService
from restro_billing.features.menu.application.menu_service import MenuService
from restro_billing.features.orders.application.order_service import OrderService
from restro_billing.features.reporting.application.revenue_service import RevenueReportService

logger = get_logger(__name__)

router = APIRouter()


@router.post("/orders")
def create_order(
    body: CreateOrderBody,
    tenant_id: Annotated[str, Depends(get_effective_tenant_id)],
    _: Annotated[str, Depends(require_roles("manager", "cashier"))],
    svc: Annotated[OrderService, Depends(get_order_service)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict:
    """
    Description: Create order + KOT for tenant.

    Inputs:
        body: Validated JSON body.
        tenant_id: From X-Tenant-Id or default.
        svc: Injected OrderService.

    Outputs:
        dict: API response from service.

    Exceptions raised:
        Mapped globally from DomainException subclasses.
    """
    logger.info(
        "controller_create_order",
        extra={"method_name": "create_order", "layer": "controller", "status": "pending"},
    )
    lines = [line.model_dump() for line in body.lines]
    out = svc.create_order(tenant_id, body.table_no, lines, idempotency_key)
    logger.info(
        "controller_create_order_done",
        extra={"method_name": "create_order", "layer": "controller", "status": "success"},
    )
    return out


@router.patch("/orders/{order_id}/state")
def patch_order_state(
    order_id: str,
    body: OrderStatePatchBody,
    tenant_id: Annotated[str, Depends(get_effective_tenant_id)],
    _: Annotated[str, Depends(require_roles("manager", "cashier"))],
    svc: Annotated[OrderService, Depends(get_order_service)],
) -> dict:
    """Controller: order state transition."""
    logger.info(
        "controller_patch_order",
        extra={"method_name": "patch_order_state", "layer": "controller", "status": "pending"},
    )
    out = svc.transition_order(tenant_id, order_id, body.state)
    logger.info(
        "controller_patch_order_done",
        extra={"method_name": "patch_order_state", "layer": "controller", "status": "success"},
    )
    return out


@router.post("/bills")
def post_bill(
    body: CreateBillBody,
    tenant_id: Annotated[str, Depends(get_effective_tenant_id)],
    _: Annotated[str, Depends(require_roles("manager", "cashier"))],
    svc: Annotated[BillingApplicationService, Depends(get_billing_application_service)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict:
    """Controller: finalize bill."""
    logger.info(
        "controller_post_bill",
        extra={"method_name": "post_bill", "layer": "controller", "status": "pending"},
    )
    out = svc.finalize_bill(tenant_id, body.order_id, body.gstin, idempotency_key)
    logger.info(
        "controller_post_bill_done",
        extra={"method_name": "post_bill", "layer": "controller", "status": "success"},
    )
    return out


@router.post("/menu/import")
def post_menu_import(
    body: BulkMenuImportBody,
    tenant_id: Annotated[str, Depends(get_effective_tenant_id)],
    _: Annotated[str, Depends(require_roles("manager", "cashier"))],
    svc: Annotated[MenuService, Depends(get_menu_service)],
) -> dict:
    """Controller: bulk menu upsert."""
    logger.info(
        "controller_menu_import",
        extra={"method_name": "post_menu_import", "layer": "controller", "status": "pending"},
    )
    items = [i.model_dump() for i in body.items]
    out = svc.bulk_import(tenant_id, items)
    logger.info(
        "controller_menu_import_done",
        extra={"method_name": "post_menu_import", "layer": "controller", "status": "success"},
    )
    return out


@router.get("/menu/items")
def get_menu_items(
    tenant_id: Annotated[str, Depends(get_effective_tenant_id)],
    _: Annotated[str, Depends(require_roles("manager", "cashier"))],
    svc: Annotated[MenuService, Depends(get_menu_service)],
    category: str | None = None,
) -> list:
    """Controller: list menu with optional category filter."""
    return svc.list_items(tenant_id, category)


@router.get("/kds/tickets")
def get_kds_tickets(
    tenant_id: Annotated[str, Depends(get_effective_tenant_id)],
    _: Annotated[str, Depends(require_roles("manager", "cashier", "kitchen_staff"))],
    svc: Annotated[KdsService, Depends(get_kds_service)],
    limit: int = 200,
) -> list:
    """Controller: list KOT tickets."""
    return svc.list_tickets(tenant_id, limit)


@router.patch("/kds/tickets/{ticket_id}/state")
def patch_kds_state(
    ticket_id: str,
    body: KdsStateBody,
    tenant_id: Annotated[str, Depends(get_effective_tenant_id)],
    _: Annotated[str, Depends(require_roles("manager", "cashier", "kitchen_staff"))],
    svc: Annotated[KdsService, Depends(get_kds_service)],
) -> dict:
    """Controller: update kitchen ticket state."""
    return svc.update_ticket_state(tenant_id, ticket_id, body.state)


@router.get("/reports/revenue")
def get_revenue(
    tenant_id: Annotated[str, Depends(get_effective_tenant_id)],
    _: Annotated[str, Depends(require_roles("manager", "cashier"))],
    svc: Annotated[RevenueReportService, Depends(get_revenue_service)],
) -> dict:
    """Controller: revenue dashboard payload."""
    return svc.build_report(tenant_id)


@router.get("/ledger/events")
def get_ledger_events(
    tenant_id: Annotated[str, Depends(get_effective_tenant_id)],
    _: Annotated[str, Depends(require_roles("manager"))],
    svc: Annotated[LedgerQueryService, Depends(get_ledger_service)],
    limit: int = 100,
) -> list:
    """Controller: audit ledger tail."""
    return svc.list_recent(tenant_id, limit)
