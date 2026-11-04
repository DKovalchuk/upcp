"""Shared probe harness for TASK-0173 surface-observability tests.

Not a test module (``surface_probe_*`` is not collected): it holds the
probe app builder, the emission-time JSON log capture and the OTel tracer
spy used by ``test_surface_observability`` / ``test_surface_metrics``.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

from app.identity.agent_auth import agent_auth
from app.identity.web_auth import web_auth
from app.shared.logging import JSONFormatter
from fastapi import Depends, FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

PROBE_LOGGER = "app.tests.surface_probe"


class JsonCapture(logging.Handler):
    """Emission-time JSON capture: ``format()`` runs inside the request
    context, so the formatter sees the contextvars as the handler did."""

    def __init__(self) -> None:
        super().__init__()
        self.setFormatter(JSONFormatter())
        self.entries: list[dict] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.entries.append(json.loads(self.format(record)))


@contextmanager
def probe_logs() -> Iterator[JsonCapture]:
    logger = logging.getLogger(PROBE_LOGGER)
    handler = JsonCapture()
    old_level, old_propagate = logger.level, logger.propagate
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
        logger.propagate = old_propagate


def probe(request: Request) -> dict:
    logging.getLogger(PROBE_LOGGER).info("probe line")
    return {"surface_state": getattr(request.state, "api_surface", None)}


def probe_app(
    *,
    middlewares: Sequence[type[BaseHTTPMiddleware]] = (),
    routes: Sequence[tuple[str, str]] = (("/probe", "public"),),
) -> FastAPI:
    """App with the given middlewares (added in production order: first
    added = innermost) and probe routes ``[(path, kind)]`` where kind is
    ``web`` / ``agent`` / ``public`` (selects the real auth blanket)."""
    app = FastAPI()
    for mw in middlewares:
        app.add_middleware(mw)
    for path, kind in routes:
        deps: list[Depends] = []
        if kind == "web":
            deps.append(Depends(web_auth))
        elif kind == "agent":
            deps.append(Depends(agent_auth))
        app.add_api_route(path, probe, methods=["GET"], dependencies=deps)
    return app


class SpanSpy:
    def __init__(self) -> None:
        self.attributes: dict[str, object] = {}

    def set_attribute(self, key: str, value: object) -> None:
        self.attributes[key] = value

    def set_attributes(self, attributes: dict[str, object]) -> None:
        self.attributes.update(attributes)

    def set_status(self, *args: object, **kwargs: object) -> None:
        pass

    def record_exception(self, *args: object, **kwargs: object) -> None:
        pass

    def is_recording(self) -> bool:
        return True


class TracerSpy:
    """Stand-in for ``tracing_middleware.tracer``: records every span's
    attributes without a real opentelemetry pipeline."""

    def __init__(self) -> None:
        self.spans: list[SpanSpy] = []

    @contextmanager
    def start_as_current_span(self, name: str, attributes: dict | None = None):  # noqa: ANN001, ANN204
        span = SpanSpy()
        span.attributes.update(attributes or {})
        self.spans.append(span)
        yield span
