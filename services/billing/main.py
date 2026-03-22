"""
Deprecated entry shim: use `uvicorn restro_billing.main:app` (layered application package).
"""

from restro_billing.main import app

__all__ = ["app"]
