from datetime import datetime, timezone
import json
import os
import sqlite3
import uuid
from fastapi import FastAPI
from pydantic import BaseModel

DB_PATH = os.getenv("INVENTORY_DB_PATH", "/data/inventory.db")
app = FastAPI(title="Inventory Service", version="0.1.0")


class StockAdjustment(BaseModel):
    ingredient_id: str
    delta_qty: float
    unit: str
    reason: str
    actor_id: str


class TheoreticalConsumption(BaseModel):
    kot_ticket_id: str
    ingredient_id: str
    consumed_qty: float
    unit: str


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.on_event("startup")
def startup() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = conn()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS inventory_events (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    c.commit()
    c.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/inventory/adjustments")
def adjust_stock(req: StockAdjustment):
    c = conn()
    eid = str(uuid.uuid4())
    c.execute(
        "INSERT INTO inventory_events(id,event_type,payload,created_at) VALUES (?,?,?,?)",
        (eid, "STOCK_ADJUSTED", json.dumps(req.model_dump()), now_iso()),
    )
    c.commit()
    c.close()
    return {"event_id": eid}


@app.post("/inventory/theoretical-consumption")
def theoretical_consumption(req: TheoreticalConsumption):
    c = conn()
    eid = str(uuid.uuid4())
    c.execute(
        "INSERT INTO inventory_events(id,event_type,payload,created_at) VALUES (?,?,?,?)",
        (eid, "THEORETICAL_CONSUMPTION", json.dumps(req.model_dump()), now_iso()),
    )
    c.commit()
    c.close()
    return {"event_id": eid}


@app.get("/inventory/variance")
def inventory_variance(limit: int = 200):
    c = conn()
    rows = c.execute("SELECT event_type,payload,created_at FROM inventory_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(r) for r in rows]
