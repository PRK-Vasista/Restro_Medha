"""Shim: prefer `uvicorn restro_inventory.main:app`."""

from restro_inventory.main import app

__all__ = ["app"]
