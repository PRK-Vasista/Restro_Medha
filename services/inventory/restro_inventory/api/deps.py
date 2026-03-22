"""FastAPI dependencies for inventory."""

from typing import Annotated

from fastapi import Header, HTTPException, Request

from restro_inventory.config.settings import get_settings
from restro_inventory.features.inventory_events.application.inventory_service import InventoryApplicationService
from restro_inventory.infrastructure.sqlite_inventory_store import SqliteInventoryStore


def get_store(request: Request) -> SqliteInventoryStore:
    s = getattr(request.app.state, "storage", None)
    if s is None:
        raise RuntimeError("Storage not initialized")
    return s


def get_inventory_service(request: Request) -> InventoryApplicationService:
    return InventoryApplicationService(get_store(request))


def require_manager(x_role: Annotated[str | None, Header(alias="X-Role")] = None) -> str:
    if not x_role or x_role.lower() != "manager":
        raise HTTPException(status_code=403, detail={"error": "insufficient_role", "error_code": "RBAC_DENIED"})
    return x_role.lower()


def effective_tenant(x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None) -> str:
    s = get_settings()
    t = (x_tenant_id or s.default_tenant_id).strip()
    return t or s.default_tenant_id
