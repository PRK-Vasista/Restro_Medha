"""
File: structured_logging.py
Purpose: Structured JSON logging helpers for all layers.
Responsibilities: Configure root logger; correlate logs via contextvars (request_id, tenant_id).
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from restro_billing.config.settings import get_settings

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
tenant_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("tenant_id", default=None)


class JsonFormatter(logging.Formatter):
    """
    Class: JsonFormatter
    Description: Emits one JSON object per log line for ingestion by Loki/ELK/etc.

    Attributes:
        service_name: Injected into every record.

    Example usage:
        handler.setFormatter(JsonFormatter("billing"))
    """

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """
        Description: Build JSON payload from LogRecord and contextvars.

        Inputs:
            record: Standard library log record.

        Outputs:
            str: Single-line JSON.

        Exceptions raised:
            None
        """
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
        for key in ("layer", "duration_ms"):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val
        ed = getattr(record, "extra_dict", None)
        if isinstance(ed, dict):
            payload.update(ed)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """
    Description: Idempotently attach JSON (or plain) handler to root logger.

    Inputs:
        None

    Outputs:
        None

    Exceptions raised:
        None
    """
    settings = get_settings()
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(JsonFormatter(settings.service_name))
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Description: Return a named logger after ensuring configuration.

    Inputs:
        name: Usually __name__ of the calling module.

    Outputs:
        logging.Logger: Configured logger.

    Exceptions raised:
        None
    """
    configure_logging()
    return logging.getLogger(name)
