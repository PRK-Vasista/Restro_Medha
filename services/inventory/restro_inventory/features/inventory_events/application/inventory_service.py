"""Inventory event use cases (business logic layer)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from restro_observability import get_logger
from restro_inventory.core.protocols.inventory_storage import InventoryStoragePort

logger = get_logger(__name__)


class InventoryApplicationService:
    """Records stock adjustments and theoretical consumption as events."""

    def __init__(self, storage: InventoryStoragePort) -> None:
        self._storage = storage

    def record_adjustment(self, tenant_id: str, payload: dict[str, Any]) -> dict[str, str]:
        """Append STOCK_ADJUSTED event."""
        logger.info("record_adjustment_enter", extra={"method_name": "record_adjustment", "layer": "service"})
        eid = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        self._storage.append_event(tenant_id, "STOCK_ADJUSTED", payload, eid, ts)
        logger.info("record_adjustment_exit", extra={"method_name": "record_adjustment", "layer": "service", "status": "success"})
        return {"event_id": eid}

    def record_theoretical_consumption(self, tenant_id: str, payload: dict[str, Any]) -> dict[str, str]:
        """Append THEORETICAL_CONSUMPTION event."""
        eid = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        self._storage.append_event(tenant_id, "THEORETICAL_CONSUMPTION", payload, eid, ts)
        return {"event_id": eid}

    def list_variance_tail(self, tenant_id: str, limit: int) -> list[dict[str, Any]]:
        """Read recent events for variance UI."""
        return self._storage.list_events(tenant_id, limit)
