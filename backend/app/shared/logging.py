"""Structured JSON logging with correlation IDs and context variables."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variables for request-scoped data
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
agent_id_var: ContextVar[str | None] = ContextVar("agent_id", default=None)


class JSONFormatter(logging.Formatter):
    """JSON log formatter with structured fields."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add correlation IDs from context
        request_id = request_id_var.get()
        if request_id:
            log_entry["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_entry["user_id"] = user_id

        agent_id = agent_id_var.get()
        if agent_id:
            log_entry["agent_id"] = agent_id

        # Add source location for DEBUG
        if record.levelno == logging.DEBUG:
            log_entry["file"] = record.pathname
            log_entry["line"] = record.lineno

        # Add exception info if present
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        # Add extra fields
        for key in ("entity_type", "entity_id", "action", "status_code", "duration_ms"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging."""
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
