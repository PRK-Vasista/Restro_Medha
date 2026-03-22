"""
File: deps.py
Purpose: FastAPI dependency providers (wiring only, no business rules).
Responsibilities: Expose storage + application services + RBAC helpers.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException, Request

from restro_billing.config.settings import get_settings
from restro_billing.features.billing_flow.application.billing_service import BillingApplicationService
from restro_billing.features.kitchen_display.application.kds_service import KdsService
from restro_billing.features.ledger.application.ledger_service import LedgerQueryService
from restro_billing.features.menu.application.menu_service import MenuService
from restro_billing.features.orders.application.order_service import OrderService
from restro_billing.features.reporting.application.revenue_service import RevenueReportService
from restro_billing.infrastructure.persistence.sqlite_billing_store import SqliteBillingStore


def get_storage(request: Request) -> SqliteBillingStore:
    """
    Description: Return process-scoped SQLite store attached at app startup.

    Inputs:
        request: Active HTTP request.

    Outputs:
        SqliteBillingStore: Shared store instance.

    Exceptions raised:
        RuntimeError: If lifespan did not initialize storage.
    """
    store = getattr(request.app.state, "storage", None)
    if store is None:
        raise RuntimeError("Storage not initialized")
    return store


def get_order_service(request: Request) -> OrderService:
    """DI: OrderService bound to app storage and settings."""
    return OrderService(get_storage(request), get_settings())


def get_billing_application_service(request: Request) -> BillingApplicationService:
    """DI: Billing finalize service."""
    return BillingApplicationService(get_storage(request), get_settings())


def get_menu_service(request: Request) -> MenuService:
    """DI: Menu service."""
    return MenuService(get_storage(request))


def get_kds_service(request: Request) -> KdsService:
    """DI: KDS service."""
    return KdsService(get_storage(request))


def get_revenue_service(request: Request) -> RevenueReportService:
    """DI: Reporting service."""
    return RevenueReportService(get_storage(request))


def get_ledger_service(request: Request) -> LedgerQueryService:
    """DI: Ledger query service."""
    return LedgerQueryService(get_storage(request))


def require_roles(*allowed: str):
    """
    Description: Factory for FastAPI dependencies that enforce X-Role header.

    Inputs:
        *allowed: Lowercase role names permitted.

    Outputs:
        Callable dependency returning normalized role string.

    Exceptions raised:
        HTTPException: 403 if role missing or not allowed.
    """

    allowed_set = {a.lower() for a in allowed}

    def _inner(x_role: Annotated[str | None, Header(alias="X-Role")] = None) -> str:
        if not x_role or x_role.lower() not in allowed_set:
            raise HTTPException(status_code=403, detail={"error": "insufficient_role", "error_code": "RBAC_DENIED"})
        return x_role.lower()

    return _inner


def get_effective_tenant_id(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    settings: Settings | None = None,
) -> str:
    """
    Description: Resolve tenant from header with config default (defense in depth at service ingress).

    Inputs:
        x_tenant_id: Optional client-provided tenant.
        settings: Optional settings override for tests.

    Outputs:
        str: Non-empty tenant id.

    Exceptions raised:
        None
    """
    s = settings or get_settings()
    return (x_tenant_id or s.default_tenant_id).strip() or s.default_tenant_id
