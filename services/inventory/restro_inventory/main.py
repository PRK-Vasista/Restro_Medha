"""ASGI entry for inventory microservice."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from restro_inventory.api.middleware import RequestContextMiddleware
from restro_inventory.api.v1.router import router as inv_router
from restro_inventory.config.settings import get_settings
from restro_observability import configure_logging, get_logger
from restro_inventory.infrastructure.sqlite_inventory_store import SqliteInventoryStore

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.service_name, log_json=settings.log_json)
    store = SqliteInventoryStore(settings)
    store.migrate()
    app.state.storage = store
    logger.info("inventory_startup", extra={"layer": "controller", "status": "success"})
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Restro Medha Inventory", version="0.2.0", lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(inv_router, prefix=f"{settings.api_v1_prefix}/inventory", tags=["v1"])
    app.include_router(inv_router, prefix="/inventory", tags=["legacy"])
    return app


app = create_app()
