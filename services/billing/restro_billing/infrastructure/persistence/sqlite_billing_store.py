"""
File: sqlite_billing_store.py
Purpose: SQLite implementation of BillingStoragePort (infrastructure layer).
Responsibilities: Migrations, transactions, SQL only — no business rules.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from restro_billing.config.settings import Settings
from restro_billing.core.logging.structured_logging import get_logger

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checksum(payload: str) -> str:
    return str(abs(hash(payload)))


class SqliteBillingStore:
    """
    Class: SqliteBillingStore
    Description: Edge SQLite adapter with tenant-scoped queries.

    Attributes:
        _settings: Injected Settings for DB path.

    Example usage:
        store = SqliteBillingStore(settings)
        store.migrate()
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._db_path = settings.billing_db_path

    def _connect(self) -> sqlite3.Connection:
        """
        Description: Open a connection with Row factory.

        Inputs:
            None

        Outputs:
            sqlite3.Connection

        Exceptions raised:
            sqlite3.Error: On disk/permission failures.
        """
        c = sqlite3.connect(self._db_path)
        c.row_factory = sqlite3.Row
        return c

    def migrate(self) -> None:
        """
        Description: Ensure schema exists and tenant_id columns are present.

        Inputs:
            None

        Outputs:
            None

        Exceptions raised:
            sqlite3.Error: On SQL failures.
        """
        os.makedirs(os.path.dirname(self._db_path) or ".", exist_ok=True)
        c = self._connect()
        try:
            c.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS ledger_events (
                    event_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL DEFAULT 'default',
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL DEFAULT 'default',
                    table_no TEXT,
                    state TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS kot_tickets (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL DEFAULT 'default',
                    order_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS bills (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL DEFAULT 'default',
                    order_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    tax_total REAL NOT NULL,
                    grand_total REAL NOT NULL,
                    gstin TEXT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS menu_items (
                    item_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL DEFAULT 'default',
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    hsn_code TEXT NOT NULL,
                    unit_price REAL NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, item_id)
                );
                CREATE TABLE IF NOT EXISTS idempotency (
                    tenant_id TEXT NOT NULL DEFAULT 'default',
                    key TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    response TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, key, endpoint)
                );
                """
            )
            self._migrate_legacy_tenant_columns(c)
            self._ensure_indexes(c)
            c.commit()
            logger.info(
                "migrate_complete",
                extra={"method_name": "migrate", "status": "success", "layer": "infrastructure"},
            )
        finally:
            c.close()

    def _migrate_legacy_tenant_columns(self, c: sqlite3.Connection) -> None:
        """
        Description: Add tenant_id to pre-SaaS SQLite files (default tenant).

        Inputs:
            c: Open connection.

        Outputs:
            None

        Exceptions raised:
            sqlite3.Error
        """
        default = "default"

        def add_col(table: str) -> None:
            cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
            if cols and "tenant_id" not in cols:
                c.execute(f"ALTER TABLE {table} ADD COLUMN tenant_id TEXT NOT NULL DEFAULT '{default}'")

        for tbl in ("ledger_events", "orders", "kot_tickets", "bills", "menu_items", "idempotency"):
            try:
                add_col(tbl)
            except sqlite3.OperationalError:
                pass

    def _ensure_indexes(self, c: sqlite3.Connection) -> None:
        """Create helpful indexes if missing."""
        for stmt in (
            "CREATE INDEX IF NOT EXISTS idx_orders_tenant ON orders(tenant_id);",
            "CREATE INDEX IF NOT EXISTS idx_kot_tenant ON kot_tickets(tenant_id);",
            "CREATE INDEX IF NOT EXISTS idx_bills_tenant ON bills(tenant_id);",
            "CREATE INDEX IF NOT EXISTS idx_ledger_tenant ON ledger_events(tenant_id);",
        ):
            c.execute(stmt)

    def _append_ledger(
        self,
        c: sqlite3.Connection,
        tenant_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        payload: dict[str, Any],
    ) -> None:
        serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        c.execute(
            """
            INSERT INTO ledger_events(event_id,tenant_id,event_type,entity_type,entity_id,payload,checksum,created_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                str(uuid.uuid4()),
                tenant_id,
                event_type,
                entity_type,
                entity_id,
                serialized,
                _checksum(serialized),
                _now_iso(),
            ),
        )

    def get_idempotent_response(self, tenant_id: str, key: str, endpoint: str) -> dict[str, Any] | None:
        c = self._connect()
        try:
            row = c.execute(
                "SELECT response FROM idempotency WHERE tenant_id=? AND key=? AND endpoint=?",
                (tenant_id, key, endpoint),
            ).fetchone()
            if row:
                return json.loads(row["response"])
            return None
        finally:
            c.close()

    def save_idempotent_response(self, tenant_id: str, key: str, endpoint: str, response: dict[str, Any]) -> None:
        c = self._connect()
        try:
            c.execute(
                "INSERT OR REPLACE INTO idempotency(tenant_id,key,endpoint,response) VALUES (?,?,?,?)",
                (tenant_id, key, endpoint, json.dumps(response)),
            )
            c.commit()
        finally:
            c.close()

    def create_order_with_kot(
        self,
        tenant_id: str,
        order_id: str,
        table_no: str | None,
        lines_payload: dict[str, Any],
        kot_id: str,
        created_at: str,
    ) -> None:
        c = self._connect()
        try:
            c.execute(
                "INSERT INTO orders(id,tenant_id,table_no,state,payload,created_at) VALUES (?,?,?,?,?,?)",
                (order_id, tenant_id, table_no, "placed", json.dumps(lines_payload), created_at),
            )
            c.execute(
                "INSERT INTO kot_tickets(id,tenant_id,order_id,state,created_at) VALUES (?,?,?,?,?)",
                (kot_id, tenant_id, order_id, "queued", created_at),
            )
            self._append_ledger(c, tenant_id, "ORDER_CREATED", "order", order_id, lines_payload)
            self._append_ledger(c, tenant_id, "KOT_CREATED", "kot_ticket", kot_id, {"order_id": order_id, "state": "queued"})
            c.commit()
            logger.info(
                "order_and_kot_persisted",
                extra={"extra_dict": {"order_id": order_id, "kot_id": kot_id}, "layer": "infrastructure", "status": "success"},
            )
        finally:
            c.close()

    def get_order_row(self, tenant_id: str, order_id: str) -> dict[str, Any] | None:
        c = self._connect()
        try:
            row = c.execute(
                "SELECT state, payload FROM orders WHERE tenant_id=? AND id=?",
                (tenant_id, order_id),
            ).fetchone()
            if not row:
                return None
            return {"state": row["state"], "payload": json.loads(row["payload"])}
        finally:
            c.close()

    def update_order_state(self, tenant_id: str, order_id: str, new_state: str, ledger_payload: dict[str, Any]) -> None:
        c = self._connect()
        try:
            c.execute(
                "UPDATE orders SET state=? WHERE tenant_id=? AND id=?",
                (new_state, tenant_id, order_id),
            )
            self._append_ledger(c, tenant_id, "ORDER_STATE_UPDATED", "order", order_id, ledger_payload)
            c.commit()
        finally:
            c.close()

    def insert_bill(
        self,
        tenant_id: str,
        bill_id: str,
        order_id: str,
        state: str,
        subtotal: float,
        tax_total: float,
        grand_total: float,
        gstin: str | None,
        payload: dict[str, Any],
        created_at: str,
        ledger_payload: dict[str, Any],
    ) -> None:
        c = self._connect()
        try:
            c.execute(
                """
                INSERT INTO bills(id,tenant_id,order_id,state,subtotal,tax_total,grand_total,gstin,payload,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    bill_id,
                    tenant_id,
                    order_id,
                    state,
                    subtotal,
                    tax_total,
                    grand_total,
                    gstin,
                    json.dumps(payload),
                    created_at,
                ),
            )
            self._append_ledger(c, tenant_id, "BILL_FINALIZED", "bill", bill_id, ledger_payload)
            c.commit()
        finally:
            c.close()

    def upsert_menu_items(self, tenant_id: str, items: list[dict[str, Any]], updated_at: str) -> int:
        c = self._connect()
        try:
            for it in items:
                c.execute(
                    """
                    INSERT OR REPLACE INTO menu_items(item_id,tenant_id,name,category,hsn_code,unit_price,updated_at)
                    VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        it["item_id"],
                        tenant_id,
                        it["name"],
                        it["category"],
                        it["hsn_code"],
                        it["unit_price"],
                        updated_at,
                    ),
                )
            self._append_ledger(c, tenant_id, "MENU_IMPORTED", "menu", "bulk", {"count": len(items)})
            c.commit()
            return len(items)
        finally:
            c.close()

    def list_menu_items(self, tenant_id: str, category: str | None) -> list[dict[str, Any]]:
        c = self._connect()
        try:
            if category:
                rows = c.execute(
                    "SELECT * FROM menu_items WHERE tenant_id=? AND category=? ORDER BY name",
                    (tenant_id, category),
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM menu_items WHERE tenant_id=? ORDER BY category,name",
                    (tenant_id,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            c.close()

    def list_kot_tickets(self, tenant_id: str, limit: int) -> list[dict[str, Any]]:
        c = self._connect()
        try:
            rows = c.execute(
                "SELECT * FROM kot_tickets WHERE tenant_id=? ORDER BY created_at DESC LIMIT ?",
                (tenant_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            c.close()

    def get_kot_row(self, tenant_id: str, ticket_id: str) -> dict[str, Any] | None:
        c = self._connect()
        try:
            row = c.execute(
                "SELECT order_id, state FROM kot_tickets WHERE tenant_id=? AND id=?",
                (tenant_id, ticket_id),
            ).fetchone()
            if not row:
                return None
            return {"order_id": row["order_id"], "state": row["state"]}
        finally:
            c.close()

    def update_kot_state(self, tenant_id: str, ticket_id: str, new_state: str, ledger_payload: dict[str, Any]) -> None:
        c = self._connect()
        try:
            c.execute(
                "UPDATE kot_tickets SET state=? WHERE tenant_id=? AND id=?",
                (new_state, tenant_id, ticket_id),
            )
            self._append_ledger(c, tenant_id, "KOT_STATE_UPDATED", "kot_ticket", ticket_id, ledger_payload)
            c.commit()
        finally:
            c.close()

    def revenue_aggregates(self, tenant_id: str) -> tuple[int, float, list[dict[str, Any]]]:
        c = self._connect()
        try:
            row = c.execute(
                "SELECT COUNT(*) AS total_bills, COALESCE(SUM(grand_total),0) AS gross_revenue FROM bills WHERE tenant_id=?",
                (tenant_id,),
            ).fetchone()
            item_rows = c.execute(
                """
                SELECT json_extract(value, '$.item_name') AS item_name, SUM(json_extract(value, '$.qty')) AS sold_qty
                FROM bills, json_each(bills.payload, '$.lines')
                WHERE bills.tenant_id=?
                GROUP BY item_name
                ORDER BY sold_qty DESC
                LIMIT 10
                """,
                (tenant_id,),
            ).fetchall()
            return int(row["total_bills"]), float(row["gross_revenue"]), [dict(r) for r in item_rows]
        finally:
            c.close()

    def list_ledger_events(self, tenant_id: str, limit: int) -> list[dict[str, Any]]:
        c = self._connect()
        try:
            rows = c.execute(
                "SELECT * FROM ledger_events WHERE tenant_id=? ORDER BY created_at DESC LIMIT ?",
                (tenant_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            c.close()
