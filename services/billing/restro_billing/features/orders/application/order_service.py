"""
File: order_service.py
Purpose: Order aggregate use cases (business logic layer).
Responsibilities: Create orders with KOT; enforce order state machine; no HTTP/SQL here.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from restro_billing.config.settings import Settings
from restro_billing.core.domain.enums import OrderState
from restro_billing.core.exceptions.order_exceptions import InvalidOrderStateTransitionException, OrderNotFoundException
from restro_observability import get_logger
from restro_billing.core.protocols.billing_storage import BillingStoragePort

logger = get_logger(__name__)

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "placed": {"in_prep", "cancelled"},
    "in_prep": {"ready", "cancelled"},
    "ready": {"served"},
    "served": set(),
    "cancelled": set(),
}


class OrderService:
    """
    Class: OrderService
    Description: Application service for dine-in order workflows.

    Attributes:
        _storage: Persistence port (injected).
        _settings: Runtime configuration (injected).

    Example usage:
        svc = OrderService(store, settings)
        svc.create_order("default", "T1", [{"item_id": "x", ...}], "idem-key")
    """

    def __init__(self, storage: BillingStoragePort, settings: Settings) -> None:
        self._storage = storage
        self._settings = settings

    def create_order(
        self,
        tenant_id: str,
        table_no: str | None,
        lines: list[dict[str, Any]],
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        """
        Description: Create a new order and paired KOT ticket; supports idempotent retries.

        Inputs:
            tenant_id: SaaS tenant scope.
            table_no: Optional table label.
            lines: List of line dicts (item_id, item_name, qty, unit_price).
            idempotency_key: Optional client dedupe key.

        Outputs:
            dict: {order_id, state, kot_ticket_id}

        Exceptions raised:
            None (storage errors propagate as exceptions — mapped at API boundary).
        """
        logger.info(
            "create_order_enter",
            extra={"method_name": "create_order", "layer": "service", "status": "pending"},
        )
        endpoint = "/orders"
        if idempotency_key:
            cached = self._storage.get_idempotent_response(tenant_id, idempotency_key, endpoint)
            if cached is not None:
                logger.info(
                    "create_order_idempotent_hit",
                    extra={"method_name": "create_order", "layer": "service", "status": "success"},
                )
                return cached

        order_id = str(uuid.uuid4())
        kot_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        payload = {"table_no": table_no, "lines": lines}
        self._storage.create_order_with_kot(tenant_id, order_id, table_no, payload, kot_id, created_at)
        resp = {"order_id": order_id, "state": OrderState.placed.value, "kot_ticket_id": kot_id}
        if idempotency_key:
            self._storage.save_idempotent_response(tenant_id, idempotency_key, endpoint, resp)
        logger.info(
            "create_order_exit",
            extra={"method_name": "create_order", "layer": "service", "status": "success"},
        )
        return resp

    def transition_order(self, tenant_id: str, order_id: str, to_state: OrderState) -> dict[str, Any]:
        """
        Description: Move order along the allowed FSM edges.

        Inputs:
            tenant_id: SaaS tenant scope.
            order_id: Target order UUID.
            to_state: Desired OrderState.

        Outputs:
            dict: {order_id, state}

        Exceptions raised:
            OrderNotFoundException: Missing order.
            InvalidOrderStateTransitionException: Illegal edge.
        """
        logger.info(
            "transition_order_enter",
            extra={"method_name": "transition_order", "layer": "service", "status": "pending"},
        )
        row = self._storage.get_order_row(tenant_id, order_id)
        if row is None:
            logger.info(
                "transition_order_not_found",
                extra={"method_name": "transition_order", "layer": "service", "status": "failure"},
            )
            raise OrderNotFoundException(tenant_id, order_id)
        current = row["state"]
        if to_state.value not in _ALLOWED_TRANSITIONS.get(current, set()):
            raise InvalidOrderStateTransitionException(tenant_id, order_id, current, to_state.value)
        self._storage.update_order_state(
            tenant_id,
            order_id,
            to_state.value,
            {"from": current, "to": to_state.value},
        )
        logger.info(
            "transition_order_exit",
            extra={"method_name": "transition_order", "layer": "service", "status": "success"},
        )
        return {"order_id": order_id, "state": to_state.value}
