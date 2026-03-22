"""
File: middleware.py
Purpose: Cross-cutting HTTP concerns for the API layer.
Responsibilities: Propagate correlation + tenant into logging contextvars.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from restro_billing.config.settings import get_settings
from restro_observability import request_id_ctx, tenant_id_ctx


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Class: RequestContextMiddleware
    Description: Injects request_id and tenant_id into contextvars for structured logs.

    Attributes:
        None

    Example usage:
        app.add_middleware(RequestContextMiddleware)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Description: Set context, call downstream, echo request id on response.

        Inputs:
            request: Incoming ASGI request.
            call_next: Next middleware/handler.

        Outputs:
            Response: Downstream response with X-Request-Id header.

        Exceptions raised:
            None
        """
        settings = get_settings()
        rid = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        tid = request.headers.get("X-Tenant-Id") or settings.default_tenant_id
        token_rid = request_id_ctx.set(rid)
        token_tid = tenant_id_ctx.set(tid)
        try:
            response = await call_next(request)
            response.headers["X-Request-Id"] = rid
            return response
        finally:
            request_id_ctx.reset(token_rid)
            tenant_id_ctx.reset(token_tid)
