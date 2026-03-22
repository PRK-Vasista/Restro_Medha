"""
File: ledger_service.py
Purpose: Ledger read use cases (business logic layer).
Responsibilities: Paginated-style event listing for audit UI.
"""

from __future__ import annotations

from typing import Any

from restro_observability import get_logger
from restro_billing.core.protocols.billing_storage import BillingStoragePort

logger = get_logger(__name__)


class LedgerQueryService:
    """
    Class: LedgerQueryService
    Description: Read-only access to append-only ledger.

    Attributes:
        _storage: Persistence port.

    Example usage:
        LedgerQueryService(store).list_recent(tenant_id, 100)
    """

    def __init__(self, storage: BillingStoragePort) -> None:
        self._storage = storage

    def list_recent(self, tenant_id: str, limit: int) -> list[dict[str, Any]]:
        """
        Description: Return newest ledger events for a tenant.

        Inputs:
            tenant_id: SaaS tenant scope.
            limit: Max events.

        Outputs:
            list[dict]: Ledger rows.

        Exceptions raised:
            None
        """
        logger.info(
            "ledger_list_enter",
            extra={"method_name": "list_recent", "layer": "service", "status": "pending"},
        )
        rows = self._storage.list_ledger_events(tenant_id, limit)
        logger.info(
            "ledger_list_exit",
            extra={"method_name": "list_recent", "layer": "service", "status": "success"},
        )
        return rows
