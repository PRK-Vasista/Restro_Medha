"""REST controllers for inventory (no business logic)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from restro_inventory.api.deps import effective_tenant, get_inventory_service, require_manager
from restro_inventory.api.v1.schemas import StockAdjustmentBody, TheoreticalConsumptionBody
from restro_inventory.features.inventory_events.application.inventory_service import InventoryApplicationService

router = APIRouter()


@router.post("/adjustments")
def post_adjustment(
    body: StockAdjustmentBody,
    tenant_id: Annotated[str, Depends(effective_tenant)],
    _: Annotated[str, Depends(require_manager)],
    svc: Annotated[InventoryApplicationService, Depends(get_inventory_service)],
) -> dict:
    return svc.record_adjustment(tenant_id, body.model_dump())


@router.post("/theoretical-consumption")
def post_theoretical(
    body: TheoreticalConsumptionBody,
    tenant_id: Annotated[str, Depends(effective_tenant)],
    _: Annotated[str, Depends(require_manager)],
    svc: Annotated[InventoryApplicationService, Depends(get_inventory_service)],
) -> dict:
    return svc.record_theoretical_consumption(tenant_id, body.model_dump())


@router.get("/variance")
def get_variance(
    tenant_id: Annotated[str, Depends(effective_tenant)],
    _: Annotated[str, Depends(require_manager)],
    svc: Annotated[InventoryApplicationService, Depends(get_inventory_service)],
    limit: int = 200,
) -> list:
    return svc.list_variance_tail(tenant_id, limit)
