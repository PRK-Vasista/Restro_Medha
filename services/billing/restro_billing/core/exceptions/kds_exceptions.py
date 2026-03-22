"""
File: kds_exceptions.py
Purpose: Kitchen display (KOT) domain errors.
Responsibilities: Unknown ticket or invalid kitchen workflow state.
"""

from restro_billing.core.exceptions.base_exception import DomainException


class KotTicketNotFoundException(DomainException):
    """Raised when a KOT ticket id is unknown."""

    error_code = "KOT_TICKET_NOT_FOUND"
    http_status = 404

    def __init__(self, tenant_id: str, ticket_id: str) -> None:
        super().__init__(
            "KOT ticket not found",
            context={"tenant_id": tenant_id, "ticket_id": ticket_id},
        )


class InvalidKdsStateException(DomainException):
    """Raised when kitchen sends an unknown status value."""

    error_code = "INVALID_KDS_STATE"
    http_status = 400

    def __init__(self, tenant_id: str, state: str) -> None:
        super().__init__(
            "Invalid KDS state",
            context={"tenant_id": tenant_id, "state": state},
        )
