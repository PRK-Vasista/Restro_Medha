"""Domain-level inventory errors."""

from typing import Any


class InventoryDomainException(Exception):
    """Base inventory domain error with HTTP mapping support."""

    error_code: str = "INVENTORY_ERROR"
    http_status: int = 400

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        self.message = message
        self.context = context or {}
        super().__init__(message)

    def to_payload(self) -> dict[str, Any]:
        return {"error": self.message, "error_code": self.error_code, "context": self.context}
