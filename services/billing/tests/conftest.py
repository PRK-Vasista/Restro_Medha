"""Pytest fixtures for billing service tests."""

import pytest

from restro_billing.config.settings import Settings


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    """File-backed SQLite so each store connection shares the same database."""
    db_path = tmp_path / "billing_test.db"
    return Settings(
        billing_db_path=str(db_path),
        default_tenant_id="test_tenant",
        gst_combined_rate=0.05,
        api_v1_prefix="/v1",
        log_json=False,
    )
