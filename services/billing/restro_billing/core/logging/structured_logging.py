"""Compatibility shim — prefer `restro_observability` directly."""

from restro_observability import (  # noqa: F401
    JsonFormatter,
    configure_logging,
    get_logger,
    request_id_ctx,
    tenant_id_ctx,
)
