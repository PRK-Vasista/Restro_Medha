"""Abstract persistence port for inventory events."""

from __future__ import annotations

from typing import Any, Protocol


class InventoryStoragePort(Protocol):
    """Port for append-only inventory event storage."""

    def migrate(self) -> None: ...

    def append_event(self, tenant_id: str, event_type: str, payload: dict[str, Any], event_id: str, created_at: str) -> None: ...

    def list_events(self, tenant_id: str, limit: int) -> list[dict[str, Any]]: ...
