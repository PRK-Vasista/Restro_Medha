"""
File: exception_handlers.py
Purpose: Map domain errors to HTTP (controller boundary hygiene).
Responsibilities: Never leak raw Python exceptions as API contracts.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from restro_billing.core.exceptions.base_exception import DomainException
from restro_observability import get_logger

logger = get_logger(__name__)


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """
    Description: Serialize DomainException to JSON with correct status.

    Inputs:
        request: Current request (for logging context).
        exc: Raised domain error.

    Outputs:
        JSONResponse: Client-safe payload.

    Exceptions raised:
        None
    """
    logger.warning(
        "domain_exception",
        extra={
            "method_name": "domain_exception_handler",
            "layer": "controller",
            "status": "failure",
            "extra_dict": exc.to_payload(),
        },
    )
    return JSONResponse(status_code=exc.http_status, content=exc.to_payload())


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Description: Catch-all for unexpected failures (logged with stack trace).

    Inputs:
        request: Current request.
        exc: Any unhandled exception.

    Outputs:
        JSONResponse: Generic 500.

    Exceptions raised:
        None
    """
    logger.exception(
        "unhandled_exception",
        extra={"method_name": "unhandled_exception_handler", "layer": "controller", "status": "failure"},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "error_code": "INTERNAL_ERROR",
            "context": {},
        },
    )
