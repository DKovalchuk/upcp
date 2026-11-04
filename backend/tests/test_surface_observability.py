"""Surface-aware observability: correlation + logs + spans — TASK-0173.

Red → green: ``surface_var``, ``sanitize_request_id`` and the surface-aware
behaviors (header prefix, span attribute) did not exist before this task —
the module-level imports made the RED phase a collection error (the
``test_web_auth_dependency`` precedent), and the behavioral cases failed
per assertion once collectable.

Covers: header prefixes for web/agent/public + ``none`` for unresolvable,
hostile ``X-Request-ID`` sanitization (newline/ANSI/overlong must not
round-trip), surface in structured logs (emission-time JSON capture),
span attributes via a tracer spy, and 401-denial attribution (surface set
at the auth dependency's ENTRY). Metrics labels: test_surface_metrics.
"""

from __future__ import annotations

import json
import logging
import re
from uuid import UUID

import pytest
from app.shared.config import get_settings
from app.shared.correlation import CorrelationMiddleware, sanitize_request_id
from app.shared.logging import JSONFormatter, surface_var
from app.shared.tracing_middleware import TracingMiddleware
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from tests.surface_probe_harness import (
    TracerSpy,
    probe,
    probe_app,
    probe_logs,
)

_HEADER_RE = re.compile(r"^(web|agent|public|none):[A-Za-z0-9._-]{1,64}$")
_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_MIDDLEWARES = (TracingMiddleware, CorrelationMiddleware)

# ── Correlation: header prefixes per surface ──────────────────────────────


@pytest.mark.parametrize(
    "kind",
    ["web", "agent", "public"],
    ids=["web", "agent", "public"],
)
def test_request_id_carries_surface_prefix(kind: str) -> None:
    assert get_settings().disable_auth is True, "precondition: hermetic mode"
    app = probe_app(middlewares=_MIDDLEWARES, routes=(("/probe", kind),))
    resp = TestClient(app).get("/probe")
    assert resp.status_code == 200, resp.text
    header = resp.headers["X-Request-ID"]
    assert header.startswith(f"{kind}:"), header
    assert _HEADER_RE.match(header), header


def test_unresolved_route_gets_none_prefix() -> None:
    app = probe_app(middlewares=_MIDDLEWARES)
    resp = TestClient(app).get("/definitely-missing")
    assert resp.status_code == 404
    header = resp.headers["X-Request-ID"]
    assert header.startswith("none:"), header
    assert _HEADER_RE.match(header), header


def test_denied_web_request_is_still_attributed(monkeypatch: pytest.MonkeyPatch) -> None:
    """401 from the blanket (before the handler) must carry the web prefix —
    the surface is set at the auth dependency's ENTRY."""
    monkeypatch.setattr(get_settings(), "disable_auth", False)
    app = probe_app(middlewares=_MIDDLEWARES, routes=(("/probe", "web"),))
    resp = TestClient(app).get("/probe")
    assert resp.status_code == 401, resp.text
    header = resp.headers["X-Request-ID"]
    assert header.startswith("web:"), header
    assert _HEADER_RE.match(header), header


# ── Correlation: hostile incoming request ids (log-injection hardening) ───


def test_sanitize_preserves_valid_client_id() -> None:
    assert sanitize_request_id("my.custom_id-123") == "my.custom_id-123"


def test_sanitize_rejects_none_and_regenerates() -> None:
    assert _ID_RE.match(sanitize_request_id(None))
    assert sanitize_request_id("") != ""


@pytest.mark.parametrize(
    "hostile",
    [
        "abc\nX-Injected: pwn",
        "abc\r\nX-Injected: pwn",
        "\x1b[31mansi-red\x1b[0m",
        "id with spaces",
        "x" * 65,
    ],
    ids=["newline", "crlf", "ansi", "spaces", "overlong"],
)
def test_sanitize_regenerates_hostile_ids(hostile: str) -> None:
    out = sanitize_request_id(hostile)
    assert out != hostile, "hostile payload must never survive"
    assert _ID_RE.match(out), out


@pytest.mark.parametrize(
    "hostile",
    ["\x1b[31mfake\x1b[0m", "x" * 65, "id with spaces"],
    ids=["ansi", "overlong", "spaces"],
)
def test_hostile_header_does_not_round_trip(hostile: str) -> None:
    app = probe_app(middlewares=_MIDDLEWARES)
    resp = TestClient(app).get("/probe", headers={"X-Request-ID": hostile})
    header = resp.headers["X-Request-ID"]
    assert header != f"public:{hostile}"
    assert hostile not in header
    assert _HEADER_RE.match(header), header


def test_valid_client_header_round_trips_under_prefix() -> None:
    app = probe_app(middlewares=_MIDDLEWARES)
    resp = TestClient(app).get("/probe", headers={"X-Request-ID": "my.custom_id-123"})
    assert resp.headers["X-Request-ID"] == "public:my.custom_id-123"


# ── Structured logs: surface contextvar ───────────────────────────────────


def test_formatter_emits_surface_field() -> None:
    token = surface_var.set("agent")
    try:
        record = logging.LogRecord("t", logging.INFO, "", 0, "msg", (), None)
        data = json.loads(JSONFormatter().format(record))
        assert data["surface"] == "agent"
    finally:
        surface_var.reset(token)


def test_surface_appears_in_logs_of_web_request() -> None:
    assert get_settings().disable_auth is True, "precondition: hermetic mode"
    app = probe_app(middlewares=_MIDDLEWARES, routes=(("/probe", "web"),))
    with probe_logs() as capture:
        resp = TestClient(app).get("/probe")
    assert resp.status_code == 200, resp.text
    assert capture.entries, "route must have logged"
    entry = capture.entries[-1]
    assert entry["surface"] == "web", entry
    header_id = resp.headers["X-Request-ID"].split(":", 1)[1]
    assert entry["request_id"] == header_id, "log request_id must match the header id"


def test_public_route_logs_carry_no_leaked_surface() -> None:
    """No leak across requests: the public route's logs have no ``surface``
    (only the auth blankets set the contextvar) and ``surface_var`` is
    clear in the test context after the request."""
    assert get_settings().disable_auth is True, "precondition: hermetic mode"
    app = probe_app(
        middlewares=_MIDDLEWARES,
        routes=(("/webprobe", "web"), ("/pubprobe", "public")),
    )
    client = TestClient(app)
    with probe_logs() as capture:
        client.get("/webprobe")
        client.get("/pubprobe")
    assert len(capture.entries) == 2
    assert capture.entries[0]["surface"] == "web"
    assert "surface" not in capture.entries[1], capture.entries[1]
    assert surface_var.get() is None


# ── OTel span attributes (tracer spy) ─────────────────────────────────────


def test_span_carries_upcp_auth_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.shared.tracing_middleware as tracing_mod

    spy = TracerSpy()
    monkeypatch.setattr(tracing_mod, "tracer", spy)
    assert get_settings().disable_auth is True, "precondition: hermetic mode"
    app = probe_app(middlewares=_MIDDLEWARES, routes=(("/probe", "web"),))
    resp = TestClient(app).get("/probe")
    assert resp.status_code == 200, resp.text
    attrs = spy.spans[0].attributes
    assert attrs["upcp.auth.surface"] == "web", attrs
    assert attrs["http.status_code"] == 200, attrs


def test_span_carries_principal_type_when_authenticated(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.shared.tracing_middleware as tracing_mod

    spy = TracerSpy()
    monkeypatch.setattr(tracing_mod, "tracer", spy)
    monkeypatch.setattr(get_settings(), "disable_auth", True)

    async def stub_user(request: Request) -> None:
        request.state.auth_type = "user"
        request.state.user_id = "u1"

    app = FastAPI()
    app.add_middleware(TracingMiddleware)
    app.add_api_route("/probe", probe, methods=["GET"], dependencies=[Depends(stub_user)])
    resp = TestClient(app).get("/probe")
    assert resp.status_code == 200, resp.text
    attrs = spy.spans[0].attributes
    assert attrs["upcp.auth.principal_type"] == "user", attrs


# ── Boundary sanity: the contextvar is request-scoped ─────────────────────


def test_surface_var_default_is_none() -> None:
    assert surface_var.get() is None


def test_generated_ids_are_uuid4_shaped() -> None:
    generated = sanitize_request_id(None)
    assert str(UUID(generated)) == generated
