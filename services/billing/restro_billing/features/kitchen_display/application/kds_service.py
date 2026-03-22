"""
File: kds_service.py
Purpose: Kitchen display (KOT) use cases (business logic layer).
Responsibilities: List tickets; validate and apply kitchen state transitions.
"""

from __future__ import annotations

from typing import Any

from restro_billing.core.domain.enums import KotState
from restro_billing.core.exceptions.kds_exceptions import InvalidKdsStateException, KotTicketNotFoundException
from restro_billing.core.logging.structured_logging import get_logger
from restro_billing.core.protocols.billing_storage import BillingStoragePort

logger = get_logger(__name__)

_VALID_KOT = {s.value for s in KotState}


class KdsService:
    """
    Class: KdsService
    Description: Kitchen ticket workflow service.

    Attributes:
        _storage: Persistence port.

    Example usage:
        KdsService(store).update_ticket_state(tid, ticket_id, "preparing")
    """

    def __init__(self, storage: BillingStoragePort) -> None:
        self._storage = storage

    def list_tickets(self, tenant_id: str, limit: int) -> list[dict[str, Any]]:
        """
        Description: Newest-first KOT listing for a tenant.

        Inputs:
            tenant_id: SaaS tenant scope.
            limit: Max rows.

        Outputs:
            list[dict]: Ticket rows.

        Exceptions raised:
            None
        """
        logger.info(
            "list_kot_enter",
            extra={"method_name": "list_tickets", "layer": "service", "status": "pending"},
        )
        rows = self._storage.list_kot_tickets(tenant_id, limit)
        logger.info(
            "list_kot_exit",
            extra={"method_name": "list_tickets", "layer": "service", "status": "success"},
        )
        return rows

    def update_ticket_state(self, tenant_id: str, ticket_id: str, state: str) -> dict[str, Any]:
        """
        Description: Advance KOT state with validation.

        Inputs:
            tenant_id: SaaS tenant scope.
            ticket_id: KOT UUID.
            state: Target kitchen status string.

        Outputs:
            dict: {ticket_id, state}

        Exceptions raised:
            InvalidKdsStateException: Unknown state string.
            KotTicketNotFoundException: Missing ticket.
        """
        logger.info(
            "update_kot_enter",
            extra={"method_name": "update_ticket_state", "layer": "service", "status": "pending"},
        )
        if state not in _VALID_KOT:
            raise InvalidKdsStateException(tenant_id, state)
        row = self._storage.get_kot_row(tenant_id, ticket_id)
        if row is None:
            raise KotTicketNotFoundException(tenant_id, ticket_id)
        prev = row["state"]
        self._storage.update_kot_state(
            tenant_id,
            ticket_id,
            state,
            {"from": prev, "to": state, "order_id": row["order_id"]},
        )
        logger.info(
            "update_kot_exit",
            extra={"method_name": "update_ticket_state", "layer": "service", "status": "success"},
        )
        return {"ticket_id": ticket_id, "state": state}
