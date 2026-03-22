"""Request context middleware for inventory service."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from restro_inventory.config.settings import get_settings
from restro_observability import request_id_ctx, tenant_id_ctx


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        rid = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        tid = request.headers.get("X-Tenant-Id") or settings.default_tenant_id
        tr = request_id_ctx.set(rid)
        tt = tenant_id_ctx.set(tid)
        try:
            resp = await call_next(request)
            resp.headers["X-Request-Id"] = rid
            return resp
        finally:
            request_id_ctx.reset(tr)
            tenant_id_ctx.reset(tt)
