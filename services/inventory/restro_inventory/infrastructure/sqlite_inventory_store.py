"""SQLite implementation of inventory event log."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

from restro_inventory.config.settings import Settings
from restro_observability import get_logger

logger = get_logger(__name__)


class SqliteInventoryStore:
    """Tenant-scoped inventory SQLite adapter."""

    def __init__(self, settings: Settings) -> None:
        self._path = settings.inventory_db_path

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self._path)
        c.row_factory = sqlite3.Row
        return c

    def migrate(self) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        c = self._conn()
        try:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS inventory_events (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL DEFAULT 'default',
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            cols = [r[1] for r in c.execute("PRAGMA table_info(inventory_events)").fetchall()]
            if cols and "tenant_id" not in cols:
                c.execute("ALTER TABLE inventory_events ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default'")
            c.commit()
            logger.info("inventory_migrate_ok", extra={"layer": "infrastructure", "status": "success"})
        finally:
            c.close()

    def append_event(self, tenant_id: str, event_type: str, payload: dict[str, Any], event_id: str, created_at: str) -> None:
        c = self._conn()
        try:
            c.execute(
                "INSERT INTO inventory_events(id,tenant_id,event_type,payload,created_at) VALUES (?,?,?,?,?)",
                (event_id, tenant_id, event_type, json.dumps(payload), created_at),
            )
            c.commit()
        finally:
            c.close()

    def list_events(self, tenant_id: str, limit: int) -> list[dict[str, Any]]:
        c = self._conn()
        try:
            rows = c.execute(
                "SELECT event_type,payload,created_at FROM inventory_events WHERE tenant_id=? ORDER BY created_at DESC LIMIT ?",
                (tenant_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            c.close()
