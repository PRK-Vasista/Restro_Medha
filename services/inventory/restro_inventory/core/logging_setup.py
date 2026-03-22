"""Minimal structured JSON logging (inventory service; mirrors billing patterns)."""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from restro_inventory.config.settings import get_settings

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
tenant_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("tenant_id", default=None)


class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service_name": self._service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "method_name": getattr(record, "method_name", record.funcName),
            "status": getattr(record, "status", None),
            "request_id": request_id_ctx.get(),
            "tenant_id": tenant_id_ctx.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    s = get_settings()
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JsonFormatter(s.service_name) if s.log_json else logging.Formatter("%(levelname)s %(message)s"))
    root.addHandler(h)
    root.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
