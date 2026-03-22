"""
Integration-style unit tests for OrderService with an in-memory SQLite store.
"""

import pytest

from restro_billing.core.domain.enums import OrderState
from restro_billing.core.exceptions.order_exceptions import InvalidOrderStateTransitionException, OrderNotFoundException
from restro_billing.features.orders.application.order_service import OrderService
from restro_billing.infrastructure.persistence.sqlite_billing_store import SqliteBillingStore


def test_create_and_transition_order(test_settings):
    store = SqliteBillingStore(test_settings)
    store.migrate()
    svc = OrderService(store, test_settings)
    out = svc.create_order("test_tenant", "T1", [{"item_id": "a", "item_name": "X", "qty": 1, "unit_price": 10}], None)
    assert "order_id" in out
    oid = out["order_id"]
    svc.transition_order("test_tenant", oid, OrderState.in_prep)
    svc.transition_order("test_tenant", oid, OrderState.ready)
    svc.transition_order("test_tenant", oid, OrderState.served)


def test_order_not_found(test_settings):
    store = SqliteBillingStore(test_settings)
    store.migrate()
    svc = OrderService(store, test_settings)
    with pytest.raises(OrderNotFoundException):
        svc.transition_order("test_tenant", "missing-uuid", OrderState.in_prep)


def test_invalid_transition(test_settings):
    store = SqliteBillingStore(test_settings)
    store.migrate()
    svc = OrderService(store, test_settings)
    out = svc.create_order("test_tenant", None, [{"item_id": "a", "item_name": "X", "qty": 1, "unit_price": 10}], None)
    with pytest.raises(InvalidOrderStateTransitionException):
        svc.transition_order("test_tenant", out["order_id"], OrderState.served)
