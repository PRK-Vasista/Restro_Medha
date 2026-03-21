from datetime import datetime, timezone
from enum import Enum
import json
import os
import sqlite3
import uuid
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

DB_PATH = os.getenv("BILLING_DB_PATH", "/data/billing.db")
app = FastAPI(title="Billing Service", version="0.1.0")


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def migrate() -> None:
    c = conn()
    c.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS ledger_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            checksum TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            table_no TEXT,
            state TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS kot_tickets (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS bills (
            id TEXT PRIMARY KEY,
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
            item_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            hsn_code TEXT NOT NULL,
            unit_price REAL NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS idempotency (
            key TEXT PRIMARY KEY,
            endpoint TEXT NOT NULL,
            response TEXT NOT NULL
        );
        """
    )
    c.commit()
    c.close()


class OrderState(str, Enum):
    placed = "placed"
    in_prep = "in_prep"
    ready = "ready"
    served = "served"
    cancelled = "cancelled"


class BillState(str, Enum):
    draft = "draft"
    finalized = "finalized"
    paid = "paid"


class OrderLine(BaseModel):
    item_id: str
    item_name: str
    qty: float
    unit_price: float


class CreateOrderRequest(BaseModel):
    table_no: str | None = None
    lines: list[OrderLine] = Field(min_length=1)


class TransitionRequest(BaseModel):
    state: OrderState


class CreateBillRequest(BaseModel):
    order_id: str
    gstin: str | None = None


class MenuItemRequest(BaseModel):
    item_id: str
    name: str
    category: str
    hsn_code: str
    unit_price: float


class BulkMenuImportRequest(BaseModel):
    items: list[MenuItemRequest] = Field(min_length=1)


class KdsStateRequest(BaseModel):
    state: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def checksum(payload: str) -> str:
    return str(abs(hash(payload)))


def append_ledger(c: sqlite3.Connection, event_type: str, entity_type: str, entity_id: str, payload: dict) -> None:
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    c.execute(
        "INSERT INTO ledger_events(event_id,event_type,entity_type,entity_id,payload,checksum,created_at) VALUES (?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), event_type, entity_type, entity_id, serialized, checksum(serialized), now_iso()),
    )


def get_idempotent(c: sqlite3.Connection, key: str | None, endpoint: str):
    if not key:
        return None
    row = c.execute("SELECT response FROM idempotency WHERE key=? AND endpoint=?", (key, endpoint)).fetchone()
    if row:
        return json.loads(row["response"])
    return None


def save_idempotent(c: sqlite3.Connection, key: str | None, endpoint: str, response: dict):
    if key:
        c.execute("INSERT OR REPLACE INTO idempotency(key,endpoint,response) VALUES (?,?,?)", (key, endpoint, json.dumps(response)))


@app.on_event("startup")
def startup() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    migrate()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/orders")
def create_order(req: CreateOrderRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    c = conn()
    cached = get_idempotent(c, idempotency_key, "/orders")
    if cached:
        c.close()
        return cached

    oid = str(uuid.uuid4())
    data = req.model_dump()
    c.execute("INSERT INTO orders(id,table_no,state,payload,created_at) VALUES (?,?,?,?,?)", (oid, req.table_no, OrderState.placed.value, json.dumps(data), now_iso()))
    kot_id = str(uuid.uuid4())
    c.execute("INSERT INTO kot_tickets(id,order_id,state,created_at) VALUES (?,?,?,?)", (kot_id, oid, "queued", now_iso()))
    append_ledger(c, "ORDER_CREATED", "order", oid, data)
    append_ledger(c, "KOT_CREATED", "kot_ticket", kot_id, {"order_id": oid, "state": "queued"})
    resp = {"order_id": oid, "state": OrderState.placed.value, "kot_ticket_id": kot_id}
    save_idempotent(c, idempotency_key, "/orders", resp)
    c.commit()
    c.close()
    return resp


@app.patch("/orders/{order_id}/state")
def update_order_state(order_id: str, req: TransitionRequest):
    c = conn()
    row = c.execute("SELECT state FROM orders WHERE id=?", (order_id,)).fetchone()
    if not row:
        c.close()
        raise HTTPException(status_code=404, detail="order not found")

    allowed = {
        "placed": {"in_prep", "cancelled"},
        "in_prep": {"ready", "cancelled"},
        "ready": {"served"},
        "served": set(),
        "cancelled": set(),
    }
    current = row["state"]
    if req.state.value not in allowed[current]:
        c.close()
        raise HTTPException(status_code=409, detail=f"invalid transition from {current} to {req.state.value}")

    c.execute("UPDATE orders SET state=? WHERE id=?", (req.state.value, order_id))
    append_ledger(c, "ORDER_STATE_UPDATED", "order", order_id, {"from": current, "to": req.state.value})
    c.commit()
    c.close()
    return {"order_id": order_id, "state": req.state.value}


@app.post("/bills")
def create_bill(req: CreateBillRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    c = conn()
    cached = get_idempotent(c, idempotency_key, "/bills")
    if cached:
        c.close()
        return cached

    order = c.execute("SELECT payload,state FROM orders WHERE id=?", (req.order_id,)).fetchone()
    if not order:
        c.close()
        raise HTTPException(status_code=404, detail="order not found")

    payload = json.loads(order["payload"])
    subtotal = sum(line["qty"] * line["unit_price"] for line in payload["lines"])
    tax = round(subtotal * 0.05, 2)
    total = round(subtotal + tax, 2)

    bid = str(uuid.uuid4())
    bill_payload = {
        "invoice_number": f"RM-{int(datetime.now().timestamp())}",
        "invoice_date_time": now_iso(),
        "gstin": req.gstin,
        "lines": payload["lines"],
        "subtotal": subtotal,
        "total_taxable_value": subtotal,
        "total_cgst": round(tax / 2, 2),
        "total_sgst": round(tax / 2, 2),
        "total_igst": 0.0,
        "grand_total": total,
    }
    c.execute(
        "INSERT INTO bills(id,order_id,state,subtotal,tax_total,grand_total,gstin,payload,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (bid, req.order_id, BillState.finalized.value, subtotal, tax, total, req.gstin, json.dumps(bill_payload), now_iso()),
    )
    append_ledger(c, "BILL_FINALIZED", "bill", bid, bill_payload)

    resp = {"bill_id": bid, "state": BillState.finalized.value, "grand_total": total}
    save_idempotent(c, idempotency_key, "/bills", resp)
    c.commit()
    c.close()
    return resp


@app.post("/menu/import")
def bulk_menu_import(req: BulkMenuImportRequest):
    c = conn()
    for item in req.items:
        c.execute(
            "INSERT OR REPLACE INTO menu_items(item_id,name,category,hsn_code,unit_price,updated_at) VALUES (?,?,?,?,?,?)",
            (item.item_id, item.name, item.category, item.hsn_code, item.unit_price, now_iso()),
        )
    append_ledger(c, "MENU_IMPORTED", "menu", "bulk", {"count": len(req.items)})
    c.commit()
    c.close()
    return {"imported": len(req.items)}


@app.get("/menu/items")
def list_menu_items(category: str | None = None):
    c = conn()
    if category:
        rows = c.execute("SELECT * FROM menu_items WHERE category=? ORDER BY name", (category,)).fetchall()
    else:
        rows = c.execute("SELECT * FROM menu_items ORDER BY category,name").fetchall()
    c.close()
    return [dict(r) for r in rows]


@app.get("/kds/tickets")
def list_kds_tickets(limit: int = 200):
    c = conn()
    rows = c.execute("SELECT * FROM kot_tickets ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(r) for r in rows]


@app.patch("/kds/tickets/{ticket_id}/state")
def update_kds_state(ticket_id: str, req: KdsStateRequest):
    allowed = {"queued", "acknowledged", "preparing", "complete"}
    if req.state not in allowed:
        raise HTTPException(status_code=400, detail="invalid kds state")
    c = conn()
    row = c.execute("SELECT order_id,state FROM kot_tickets WHERE id=?", (ticket_id,)).fetchone()
    if not row:
        c.close()
        raise HTTPException(status_code=404, detail="ticket not found")
    c.execute("UPDATE kot_tickets SET state=? WHERE id=?", (req.state, ticket_id))
    append_ledger(c, "KOT_STATE_UPDATED", "kot_ticket", ticket_id, {"from": row["state"], "to": req.state, "order_id": row["order_id"]})
    c.commit()
    c.close()
    return {"ticket_id": ticket_id, "state": req.state}


@app.get("/reports/revenue")
def revenue_report():
    c = conn()
    row = c.execute("SELECT COUNT(*) AS total_bills, COALESCE(SUM(grand_total),0) AS gross_revenue FROM bills").fetchone()
    item_rows = c.execute(
        """
        SELECT json_extract(value, '$.item_name') AS item_name, SUM(json_extract(value, '$.qty')) AS sold_qty
        FROM bills, json_each(bills.payload, '$.lines')
        GROUP BY item_name
        ORDER BY sold_qty DESC
        LIMIT 10
        """
    ).fetchall()
    c.close()
    return {
        "total_bills": row["total_bills"],
        "gross_revenue": row["gross_revenue"],
        "top_selling_items": [dict(r) for r in item_rows],
    }


@app.get("/ledger/events")
def list_ledger(limit: int = 100):
    c = conn()
    rows = c.execute("SELECT * FROM ledger_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(r) for r in rows]
