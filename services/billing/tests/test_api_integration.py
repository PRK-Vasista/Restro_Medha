"""API integration tests (full stack in-process with isolated DB via env)."""

import pytest
from fastapi.testclient import TestClient

from restro_billing.config.settings import get_settings
from restro_billing.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Description: Point Settings at a temp DB and build TestClient.

    Inputs:
        tmp_path: pytest temp directory.
        monkeypatch: Env override.

    Outputs:
        TestClient: HTTP client against app.

    Exceptions raised:
        None
    """
    monkeypatch.setenv("BILLING_DB_PATH", str(tmp_path / "api.db"))
    monkeypatch.setenv("LOG_JSON", "false")
    monkeypatch.setenv("DEFAULT_TENANT_ID", "t1")
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_v1_order_flow(client: TestClient):
    r = client.post(
        "/v1/orders",
        json={"table_no": "T1", "lines": [{"item_id": "a", "item_name": "X", "qty": 1, "unit_price": 10}]},
        headers={"X-Role": "cashier", "X-Tenant-Id": "t1"},
    )
    assert r.status_code == 200
    oid = r.json()["order_id"]
    r2 = client.post(
        "/v1/bills",
        json={"order_id": oid, "gstin": None},
        headers={"X-Role": "cashier", "X-Tenant-Id": "t1"},
    )
    assert r2.status_code == 200
    assert "bill_id" in r2.json()


def test_rbac_denied(client: TestClient):
    r = client.post(
        "/v1/orders",
        json={"table_no": "T1", "lines": [{"item_id": "a", "item_name": "X", "qty": 1, "unit_price": 10}]},
        headers={"X-Role": "kitchen_staff"},
    )
    assert r.status_code == 403
