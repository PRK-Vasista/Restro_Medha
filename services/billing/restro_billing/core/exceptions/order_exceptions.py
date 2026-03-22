"""
File: order_exceptions.py
Purpose: Order aggregate domain errors.
Responsibilities: Typed exceptions for missing orders and invalid transitions.
"""

from restro_billing.core.exceptions.base_exception import DomainException


class OrderNotFoundException(DomainException):
    """Raised when an order id does not exist for the tenant."""

    error_code = "ORDER_NOT_FOUND"
    http_status = 404

    def __init__(self, tenant_id: str, order_id: str) -> None:
        super().__init__(
            "Order not found",
            context={"tenant_id": tenant_id, "order_id": order_id},
        )


class InvalidOrderStateTransitionException(DomainException):
    """Raised when a disallowed FSM transition is requested."""

    error_code = "INVALID_ORDER_STATE_TRANSITION"
    http_status = 409

    def __init__(self, tenant_id: str, order_id: str, from_state: str, to_state: str) -> None:
        super().__init__(
            f"Invalid transition from {from_state} to {to_state}",
            context={
                "tenant_id": tenant_id,
                "order_id": order_id,
                "from_state": from_state,
                "to_state": to_state,
            },
        )
