"""Metrics ``surface`` label — TASK-0173 (SPEC-0028 §3.6 / AC9).

Red → green: before this task ``upcp_http_requests_total`` /
``upcp_http_request_duration_seconds`` had no ``surface`` label, so the
registry lookups below returned ``None`` and the deltas failed.

The label is ADDITIVE: existing aggregate dashboards keep working, exact
label matches must include ``surface``, series cardinality grows.
"""

from __future__ import annotations

import pytest
from app.shared.config import get_settings
from app.shared.metrics_middleware import MetricsMiddleware
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from tests.surface_probe_harness import probe_app


def _counter(handler: str, surface: str, status: str) -> float | None:
    return REGISTRY.get_sample_value(
        "upcp_http_requests_total",
        {"method": "GET", "handler": handler, "status": status, "surface": surface},
    )


def test_requests_total_counter_carries_surface_label() -> None:
    assert get_settings().disable_auth is True, "precondition: hermetic mode"
    app = probe_app(middlewares=(MetricsMiddleware,), routes=(("/api/v1/xyzweb", "web"),))
    handler = "/api/v1/xyzweb"
    before = _counter(handler, "web", "200") or 0.0
    resp = TestClient(app).get(handler)
    assert resp.status_code == 200, resp.text
    assert _counter(handler, "web", "200") == before + 1


def test_duration_histogram_carries_surface_label() -> None:
    assert get_settings().disable_auth is True, "precondition: hermetic mode"
    app = probe_app(middlewares=(MetricsMiddleware,), routes=(("/pubprobe", "public"),))
    key = {"method": "GET", "handler": "/pubprobe", "surface": "public"}
    before = REGISTRY.get_sample_value("upcp_http_request_duration_seconds_count", key) or 0.0
    resp = TestClient(app).get("/pubprobe")
    assert resp.status_code == 200, resp.text
    assert REGISTRY.get_sample_value("upcp_http_request_duration_seconds_count", key) == before + 1


def test_denied_request_metrics_keep_web_surface_label(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 401-denied request is still a web-surface request in the metrics."""
    monkeypatch.setattr(get_settings(), "disable_auth", False)
    app = probe_app(middlewares=(MetricsMiddleware,), routes=(("/api/v1/denyprobe", "web"),))
    handler = "/api/v1/denyprobe"
    before = _counter(handler, "web", "401") or 0.0
    resp = TestClient(app).get(handler)
    assert resp.status_code == 401, resp.text
    assert _counter(handler, "web", "401") == before + 1


def test_unattributed_404_labeled_none() -> None:
    app = probe_app(middlewares=(MetricsMiddleware,))
    handler = "/missing404"  # no dash → stays literal in the handler label
    before = _counter(handler, "none", "404") or 0.0
    resp = TestClient(app).get(handler)
    assert resp.status_code == 404
    assert _counter(handler, "none", "404") == before + 1
