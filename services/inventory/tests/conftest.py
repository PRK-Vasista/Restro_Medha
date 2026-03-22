"""Pytest fixtures for inventory service tests."""

import pytest

from restro_inventory.config.settings import Settings


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    """
    File-backed SQLite under pytest tmp_path (never uses /data from env defaults).

    Matches billing test pattern; requires Settings(populate_by_name=True).
    """
    return Settings(
        inventory_db_path=str(tmp_path / "inventory_test.db"),
        default_tenant_id="test_tenant",
        api_v1_prefix="/v1",
        log_json=False,
    )
