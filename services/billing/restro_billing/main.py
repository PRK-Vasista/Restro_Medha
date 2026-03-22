"""
File: main.py
Purpose: ASGI application entrypoint for the billing microservice.
Responsibilities: Lifespan wiring, middleware, routers, exception handlers, /health.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from restro_billing.api.exception_handlers import domain_exception_handler, unhandled_exception_handler
from restro_billing.api.middleware import RequestContextMiddleware
from restro_billing.api.v1.router import router as v1_router
from restro_billing.config.settings import get_settings
from restro_billing.core.exceptions.base_exception import DomainException
from restro_billing.core.logging.structured_logging import configure_logging, get_logger
from restro_billing.infrastructure.persistence.sqlite_billing_store import SqliteBillingStore

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Description: Initialize SQLite store once per worker.

    Inputs:
        app: FastAPI instance.

    Outputs:
        Yields control after migration.

    Exceptions raised:
        sqlite3.Error: If migration fails.
    """
    configure_logging()
    settings = get_settings()
    store = SqliteBillingStore(settings)
    store.migrate()
    app.state.storage = store
    logger.info(
        "app_startup",
        extra={"method_name": "lifespan", "layer": "controller", "status": "success"},
    )
    yield
    logger.info(
        "app_shutdown",
        extra={"method_name": "lifespan", "layer": "controller", "status": "success"},
    )


def create_app() -> FastAPI:
    """
    Description: Factory for FastAPI app (tests can call without global state).

    Inputs:
        None

    Outputs:
        FastAPI: Configured application.

    Exceptions raised:
        None
    """
    settings = get_settings()
    app = FastAPI(
        title="Restro Medha Billing",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/health", tags=["ops"])
    def health() -> dict:
        """Liveness probe (unversioned)."""
        return {"status": "ok"}

    app.include_router(v1_router, prefix=settings.api_v1_prefix, tags=["v1"])
    # Backward-compatible unversioned paths (same handlers)
    app.include_router(v1_router, prefix="", tags=["legacy"])

    return app


app = create_app()
