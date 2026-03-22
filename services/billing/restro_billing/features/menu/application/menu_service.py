"""
File: menu_service.py
Purpose: Menu catalog use cases (business logic layer).
Responsibilities: Bulk import and filtered listing; delegates persistence only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from restro_observability import get_logger
from restro_billing.core.protocols.billing_storage import BillingStoragePort

logger = get_logger(__name__)


class MenuService:
    """
    Class: MenuService
    Description: Manages tenant-scoped menu items.

    Attributes:
        _storage: Persistence port.

    Example usage:
        MenuService(store).bulk_import(tenant_id, items)
    """

    def __init__(self, storage: BillingStoragePort) -> None:
        self._storage = storage

    def bulk_import(self, tenant_id: str, items: list[dict[str, Any]]) -> dict[str, int]:
        """
        Description: Upsert many menu rows in one transaction scope.

        Inputs:
            tenant_id: SaaS tenant scope.
            items: Dicts with item_id, name, category, hsn_code, unit_price.

        Outputs:
            dict: {imported: count}

        Exceptions raised:
            None
        """
        logger.info(
            "bulk_import_enter",
            extra={"method_name": "bulk_import", "layer": "service", "status": "pending"},
        )
        updated_at = datetime.now(timezone.utc).isoformat()
        n = self._storage.upsert_menu_items(tenant_id, items, updated_at)
        logger.info(
            "bulk_import_exit",
            extra={"method_name": "bulk_import", "layer": "service", "status": "success"},
        )
        return {"imported": n}

    def list_items(self, tenant_id: str, category: str | None) -> list[dict[str, Any]]:
        """
        Description: Return catalog rows optionally filtered by category.

        Inputs:
            tenant_id: SaaS tenant scope.
            category: Optional filter.

        Outputs:
            list[dict]: Raw rows for API mapping.

        Exceptions raised:
            None
        """
        logger.info(
            "list_menu_enter",
            extra={"method_name": "list_items", "layer": "service", "status": "pending"},
        )
        rows = self._storage.list_menu_items(tenant_id, category)
        logger.info(
            "list_menu_exit",
            extra={"method_name": "list_items", "layer": "service", "status": "success"},
        )
        return rows
