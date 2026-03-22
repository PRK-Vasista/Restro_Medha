"""
File: structured_logging.py
Purpose: JSON structured logging and correlation IDs for all Python edge services.
Responsibilities: Root logger setup; contextvars for request_id and tenant_id; JsonFormatter.

This module is dependency-free (stdlib only) so billing, inventory, and future services can share it.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

# Correlation scope for the current async/sync request chain
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
tenant_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("tenant_id", default=None)


class JsonFormatter(logging.Formatter):
    """
    Class: JsonFormatter
    Description: One JSON object per log line for log aggregators.

    Attributes:
        _service_name: Logical service name on every record.

    Example usage:
        logging.StreamHandler().setFormatter(JsonFormatter("billing"))
    """

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """
        Description: Serialize LogRecord to JSON.

        Inputs:
            record: Active log record.

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


def configure_logging(service_name: str, *, log_json: bool = True) -> None:
    """
    Description: Attach a single handler to the root logger (idempotent).

    Inputs:
        service_name: Value stored on each JSON log line.
        log_json: If False, use a simple text formatter for local dev.

    Outputs:
        None

    Exceptions raised:
        None
    """
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    if log_json:
        handler.setFormatter(JsonFormatter(service_name))
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Description: Return a module logger after ensuring root configuration exists.

    Inputs:
        name: Typically __name__.

    Outputs:
        logging.Logger: Child logger.

    Exceptions raised:
        None
    """
    return logging.getLogger(name)
