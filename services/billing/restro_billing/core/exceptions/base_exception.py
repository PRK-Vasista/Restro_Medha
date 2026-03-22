"""
File: base_exception.py
Purpose: Root domain exception type — never leak raw exceptions to HTTP clients.
Responsibilities: Carry error_code, message, context, and suggested HTTP status.
"""

from typing import Any


class DomainException(Exception):
    """
    Class: DomainException
    Description: Base class for all billing-domain failures.

    Attributes:
        error_code: Stable machine-readable code (e.g. ORDER_NOT_FOUND).
        message: Human-readable explanation.
        context: Arbitrary structured metadata (tenant_id, ids, etc.).
        http_status: Suggested HTTP status for the API layer.

    Example usage:
        raise OrderNotFoundException(tenant_id="t1", order_id="abc")
    """

    error_code: str = "DOMAIN_ERROR"
    http_status: int = 400

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.context = context or {}
        super().__init__(message)

    def to_payload(self) -> dict[str, Any]:
        """
        Description: Serialize for JSON error responses (controller layer).

        Inputs:
            None

        Outputs:
            dict: error, error_code, context.

        Exceptions raised:
            None
        """
        return {
            "error": self.message,
            "error_code": self.error_code,
            "context": self.context,
        }
