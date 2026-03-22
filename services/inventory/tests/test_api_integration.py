"""
File: test_api_integration.py
Purpose: In-process API tests for inventory service (controller + service + SQLite).
Responsibilities: Health, versioned paths, RBAC, tenant header.
"""

import pytest
from fastapi.testclient import TestClient

from restro_inventory.config.settings import get_settings
from restro_inventory.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Description: Isolate DB and settings for each test function.

    Inputs:
        tmp_path: Pytest temp directory.
        monkeypatch: Env overrides.

    Outputs:
        TestClient: HTTP client.

    Exceptions raised:
        None
    """
    monkeypatch.setenv("INVENTORY_DB_PATH", str(tmp_path / "inv.db"))
    monkeypatch.setenv("LOG_JSON", "false")
    monkeypatch.setenv("DEFAULT_TENANT_ID", "t1")
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def test_health(client: TestClient):
    """GET /health returns ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_v1_adjustment_flow(client: TestClient):
    """Manager can post adjustment on /v1/inventory/adjustments."""
    r = client.post(
        "/v1/inventory/adjustments",
        json={
            "ingredient_id": "ing-1",
            "delta_qty": -2.5,
            "unit": "kg",
            "reason": "spoilage",
            "actor_id": "user-1",
        },
        headers={"X-Role": "manager", "X-Tenant-Id": "t1"},
    )
    assert r.status_code == 200
    assert "event_id" in r.json()


def test_legacy_inventory_path(client: TestClient):
    """Legacy /inventory/adjustments still works."""
    r = client.post(
        "/inventory/adjustments",
        json={
            "ingredient_id": "ing-2",
            "delta_qty": 1.0,
            "unit": "kg",
            "reason": "delivery",
            "actor_id": "user-1",
        },
        headers={"X-Role": "manager", "X-Tenant-Id": "t1"},
    )
    assert r.status_code == 200


def test_rbac_denied(client: TestClient):
    """Non-manager cannot adjust stock."""
    r = client.post(
        "/v1/inventory/adjustments",
        json={
            "ingredient_id": "ing-1",
            "delta_qty": 1.0,
            "unit": "kg",
            "reason": "x",
            "actor_id": "u",
        },
        headers={"X-Role": "cashier"},
    )
    assert r.status_code == 403


def test_v1_variance_list(client: TestClient):
    """GET /v1/inventory/variance returns events after an adjustment."""
    client.post(
        "/v1/inventory/adjustments",
        json={
            "ingredient_id": "ing-var",
            "delta_qty": -0.1,
            "unit": "l",
            "reason": "spill",
            "actor_id": "user-1",
        },
        headers={"X-Role": "manager", "X-Tenant-Id": "t1"},
    )
    r = client.get("/v1/inventory/variance", headers={"X-Role": "manager", "X-Tenant-Id": "t1"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["event_type"] == "STOCK_ADJUSTED"
