"""Unit tests for InventoryApplicationService + SqliteInventoryStore."""

import pytest

from restro_inventory.features.inventory_events.application.inventory_service import InventoryApplicationService
from restro_inventory.infrastructure.sqlite_inventory_store import SqliteInventoryStore


def test_record_adjustment_and_list(test_settings):
    store = SqliteInventoryStore(test_settings)
    store.migrate()
    svc = InventoryApplicationService(store)
    out = svc.record_adjustment(
        "test_tenant",
        {
            "ingredient_id": "flour",
            "delta_qty": -1.0,
            "unit": "kg",
            "reason": "waste",
            "actor_id": "chef-1",
        },
    )
    assert "event_id" in out
    rows = svc.list_variance_tail("test_tenant", 10)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "STOCK_ADJUSTED"


def test_record_theoretical_consumption(test_settings):
    store = SqliteInventoryStore(test_settings)
    store.migrate()
    svc = InventoryApplicationService(store)
    svc.record_theoretical_consumption(
        "test_tenant",
        {
            "kot_ticket_id": "kot-1",
            "ingredient_id": "rice",
            "consumed_qty": 0.5,
            "unit": "kg",
        },
    )
    rows = svc.list_variance_tail("test_tenant", 5)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "THEORETICAL_CONSUMPTION"


def test_tenant_isolation(test_settings):
    store = SqliteInventoryStore(test_settings)
    store.migrate()
    svc = InventoryApplicationService(store)
    svc.record_adjustment("tenant_a", {"ingredient_id": "x", "delta_qty": 1, "unit": "u", "reason": "r", "actor_id": "a"})
    svc.record_adjustment("tenant_b", {"ingredient_id": "y", "delta_qty": 2, "unit": "u", "reason": "r", "actor_id": "b"})
    assert len(svc.list_variance_tail("tenant_a", 10)) == 1
    assert len(svc.list_variance_tail("tenant_b", 10)) == 1
