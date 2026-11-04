"""Rate-limit resilience — aspect-review FIX 2 (SPEC-0028 AC9 hardening).

Two contracts, red first:

- **fail-open**: a Redis outage in ``check_rate_limit`` must ALLOW the
  request with a structured ``action=ratelimit.unavailable`` warning at
  BOTH layers (floor middleware + per-surface policy) — availability
  posture matching ``identity/denylist.py``'s ``auth.denylist_unavailable``
  precedent. RED today: the raw ``ConnectionError`` escapes and the
  request 500s;
- **threadpool offload**: both callers (``SurfaceRateLimit.__call__`` and
  ``RateLimitMiddleware.dispatch``) must run the sync Redis check through
  ``starlette.concurrency.run_in_threadpool`` (the auth-deps pattern —
  no event-loop blocking). RED today: the module attributes do not exist,
  so ``monkeypatch.setattr(..., raising=True)`` errors.
"""

from __future__ import annotations

import logging

import pytest
import starlette.concurrency
from app.shared import rate_limit as rate_limit_mod
from app.shared import rate_limit_middleware as rate_limit_mw
from app.shared.config import get_settings
from app.shared.rate_limit import check_rate_limit, surface_rate_limit
from app.shared.rate_limit_middleware import RateLimitMiddleware
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


class _ExplodingRedis:
    """Any interaction raises — simulates a Redis outage."""

    def pipeline(self, transaction: bool = True):  # noqa: ARG002, ANN201
        raise ConnectionError("redis down")

    def zrem(self, *args: object, **kwargs: object) -> None:  # noqa: ARG002
        raise ConnectionError("redis down")


@pytest.fixture()
def redis_outage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rate_limit_mod, "get_redis_client", lambda: _ExplodingRedis())
    monkeypatch.setattr(get_settings(), "disable_rate_limit", False)


def _app(*, floor: bool, surface: bool) -> FastAPI:
    app = FastAPI()
    if floor:
        app.add_middleware(RateLimitMiddleware)
    deps = [Depends(surface_rate_limit("web"))] if surface else []

    def _ok() -> dict:
        return {"ok": True}

    app.add_api_route("/w", _ok, methods=["GET"], dependencies=deps)
    return app


def _actions(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [getattr(r, "action", "") for r in caplog.records]


# ── Fail-open: outage never breaks the request (both layers) ──────────────


def test_floor_layer_fails_open_on_redis_outage(
    redis_outage: None, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="app.shared.rate_limit"):
        resp = TestClient(_app(floor=True, surface=False)).get("/w")
    assert resp.status_code == 200, f"outage must fail open, got {resp.status_code}"
    assert "ratelimit.unavailable" in _actions(caplog), _actions(caplog)
    # the fail-open answer still feeds the floor's own header block
    assert resp.headers["X-RateLimit-Limit"], resp.headers


def test_surface_layer_fails_open_on_redis_outage(
    redis_outage: None, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="app.shared.rate_limit"):
        resp = TestClient(_app(floor=False, surface=True)).get("/w")
    assert resp.status_code == 200, f"outage must fail open, got {resp.status_code}"
    assert "ratelimit.unavailable" in _actions(caplog), _actions(caplog)


def test_fail_open_warning_carries_structured_context(
    redis_outage: None, caplog: pytest.LogCaptureFixture
) -> None:
    """The warning is machine-readable (action + entity_type), not free text."""
    with caplog.at_level(logging.WARNING, logger="app.shared.rate_limit"):
        result = check_rate_limit("192.168.1.1", "login")
    assert result["allowed"] is True
    assert result["retry_after"] is None
    assert result["limit"] == 5 and result["window"] == 60
    record = next(r for r in caplog.records if getattr(r, "action", "") == "ratelimit.unavailable")
    assert getattr(record, "entity_type", "") == "rate_limit"


# ── Threadpool offload: neither layer blocks the event loop ───────────────


def test_redis_check_runs_in_threadpool_in_both_layers(
    redis_outage: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[object] = []
    real = starlette.concurrency.run_in_threadpool

    async def spy(func, *args, **kwargs):  # noqa: ANN001, ANN202
        calls.append(func)
        return await real(func, *args, **kwargs)

    monkeypatch.setattr(rate_limit_mod, "run_in_threadpool", spy)  # raising by default
    monkeypatch.setattr(rate_limit_mw, "run_in_threadpool", spy)

    resp = TestClient(_app(floor=True, surface=True)).get("/w")
    assert resp.status_code == 200, resp.text
    hits = sum(1 for f in calls if f is check_rate_limit)
    assert hits >= 2, f"both layers must offload check_rate_limit, got {hits}"
