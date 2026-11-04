"""Surface rate policies — TASK-0173 / SPEC-0028 AC9 (Shape A).

Two layers, one shared implementation (Decision D2 — distinction by data,
not code copies):

- a global pre-auth IP floor in ``RateLimitMiddleware`` — EVERY path except
  an exact-path public skip set (no version prefixes anywhere: unknown and
  future prefixes are limited by default);
- a per-surface policy (``SurfaceRateLimit``) attached in
  ``include_surfaces`` right AFTER the auth dependency, keyed by principal
  when available (fallback IP) and honoring ``disable_rate_limit``.

Red → green: ``SurfaceRateLimit`` / ``surface_rate_limit`` and the
``UPCP_RATE_LIMIT_*`` settings do not exist before this task — module-level
imports make the RED phase a collection error (test_web_auth_dependency
precedent), then the behavioral cases fail per assertion.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.api.registry import AGENT_ROUTERS, PUBLIC_ROUTERS, WEB_ROUTERS, include_surfaces
from app.identity.agent_auth import agent_auth
from app.identity.web_auth import web_auth
from app.shared import rate_limit as rate_limit_mod
from app.shared.config import get_settings
from app.shared.rate_limit import SurfaceRateLimit, surface_rate_limit
from app.shared.rate_limit_middleware import RateLimitMiddleware
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

MCP_TOOLS = "/mcp/tools"
_SHARED = Path(__file__).resolve().parents[1] / "app" / "shared"

# ── Harness: keyed fake redis (per-bucket counts, E8's fake generalised) ──


class _Pipe:
    def __init__(self, redis: _KeyedRedis) -> None:
        self._redis = redis
        self._key: str | None = None

    def _track(self, key: str) -> _Pipe:
        self._key = key
        return self

    def zremrangebyscore(self, key: str, *args: object, **kwargs: object) -> _Pipe:
        return self._track(key)

    def zcard(self, key: str, *args: object, **kwargs: object) -> _Pipe:
        return self._track(key)

    def zadd(self, key: str, *args: object, **kwargs: object) -> _Pipe:
        return self._track(key)

    def expire(self, key: str, *args: object, **kwargs: object) -> _Pipe:
        return self._track(key)

    def execute(self) -> list[object]:
        count = self._redis.counts.get(self._key or "", 0)
        self._redis.counts[self._key or ""] = count + 1
        return [None, count, True, True]


class _KeyedRedis:
    """Minimal redis stand-in: sliding-window counts per key."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def pipeline(self, transaction: bool = True) -> _Pipe:  # noqa: ARG002
        return _Pipe(self)

    def zrem(self, key: str, member: object) -> None:
        if key in self.counts:
            self.counts[key] = max(0, self.counts[key] - 1)


@pytest.fixture()
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> _KeyedRedis:
    fake = _KeyedRedis()
    monkeypatch.setattr(rate_limit_mod, "get_redis_client", lambda: fake)
    return fake


@pytest.fixture()
def rate_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "disable_rate_limit", False)


def _as_user(request: Request) -> None:
    request.state.user_id = request.headers.get("X-Stub-User", "anon")


def _as_agent(request: Request) -> None:
    request.state.agent_id = request.headers.get("X-Stub-Agent", "anon")


def _rate_app(*routes: tuple[str, str | None, str | None], with_floor: bool) -> FastAPI:
    """``(path, surface | None, principal-stub | None)`` routes.

    ``surface`` attaches the per-surface policy dependency; ``principal`` a
    stub dependency standing in for the auth blanket's ``request.state``.
    """
    app = FastAPI()
    if with_floor:
        app.add_middleware(RateLimitMiddleware)
    for path, surface, principal in routes:
        deps = []
        if principal == "user":
            deps.append(Depends(_as_user))
        elif principal == "agent":
            deps.append(Depends(_as_agent))
        if surface is not None:
            deps.append(Depends(surface_rate_limit(surface)))

        def _ok() -> dict:
            return {"ok": True}

        app.add_api_route(path, _ok, methods=["GET"], dependencies=deps)
    return app


# ── Per-surface thresholds (two layers active, production shape) ──────────


def test_web_and_agent_thresholds_differ(
    fake_redis: _KeyedRedis, rate_on: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "rate_limit_web_max", 2)
    monkeypatch.setattr(get_settings(), "rate_limit_agent_max", 3)
    app = _rate_app(("/w", "web", None), ("/a", "agent", None), with_floor=True)
    client = TestClient(app)

    web = [client.get("/w").status_code for _ in range(3)]
    agent = [client.get("/a").status_code for _ in range(4)]
    assert web == [200, 200, 429], web
    assert agent == [200, 200, 200, 429], agent

    denied = client.get("/w")
    assert denied.headers["Retry-After"] == "60"
    assert denied.json() == {"detail": "Too many requests"}


def test_success_headers_report_the_surface_bucket(
    fake_redis: _KeyedRedis, rate_on: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The floor defers to the surface result stored on ``request.state`` —
    a surface-limited response shows the surface bucket, not the floor's."""
    monkeypatch.setattr(get_settings(), "rate_limit_web_max", 7)
    app = _rate_app(("/w", "web", None), with_floor=True)
    resp = TestClient(app).get("/w")
    assert resp.status_code == 200
    assert resp.headers["X-RateLimit-Limit"] == "7"


def test_principal_buckets_isolate_users_and_agents(
    fake_redis: _KeyedRedis, rate_on: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "rate_limit_web_max", 1)
    monkeypatch.setattr(get_settings(), "rate_limit_agent_max", 1)
    app = _rate_app(("/w", "web", "user"), ("/a", "agent", "agent"), with_floor=False)
    client = TestClient(app)

    alice, bob = {"X-Stub-User": "alice"}, {"X-Stub-User": "bob"}
    assert client.get("/w", headers=alice).status_code == 200
    assert client.get("/w", headers=alice).status_code == 429
    assert client.get("/w", headers=bob).status_code == 200, "independent principal buckets"

    ag1, ag2 = {"X-Stub-Agent": "agent-1"}, {"X-Stub-Agent": "agent-2"}
    assert client.get("/a", headers=ag1).status_code == 200
    assert client.get("/a", headers=ag1).status_code == 429
    assert client.get("/a", headers=ag2).status_code == 200

    assert "rate_limit:surface_web:user:alice" in fake_redis.counts
    assert "rate_limit:surface_agent:agent:agent-1" in fake_redis.counts


def test_surface_policy_inert_when_disabled(
    fake_redis: _KeyedRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``UPCP_DISABLE_RATE_LIMIT=true`` skips the per-surface check — the
    same observable parity as the middleware's registration gate in main.py."""
    monkeypatch.setattr(get_settings(), "disable_rate_limit", True)
    monkeypatch.setattr(get_settings(), "rate_limit_web_max", 1)
    app = _rate_app(("/w", "web", None), with_floor=False)
    client = TestClient(app)
    assert [client.get("/w").status_code for _ in range(4)] == [200, 200, 200, 200]
    assert fake_redis.counts == {}


# ── Floor: exact-path skip set + default-deny on unknown prefixes ─────────


def test_public_monitoring_paths_never_consume_the_floor(
    fake_redis: _KeyedRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(rate_limit_mod.DEFAULT_LIMITS, "default", (1, 60))
    app = _rate_app(("/health", None, None), ("/metrics", None, None), with_floor=True)
    client = TestClient(app)
    for _ in range(3):
        assert client.get("/health").status_code == 200
        assert client.get("/metrics").status_code == 200
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert fake_redis.counts == {}, f"skip paths must not hit redis: {fake_redis.counts}"


@pytest.mark.parametrize(
    "path",
    ["/mcp/probe", "/brand-new/thing", "/api/v2/probe"],
    ids=["mcp", "future-prefix", "api-v2"],
)
def test_unknown_prefix_is_floored_by_default(
    path: str, fake_redis: _KeyedRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Default-deny direction (AC9): no version-prefix gating — any path
    outside the exact public skip set consumes the floor bucket."""
    monkeypatch.setitem(rate_limit_mod.DEFAULT_LIMITS, "default", (1, 60))
    app = _rate_app((path, None, None), with_floor=True)
    client = TestClient(app)
    first = client.get(path)
    second = client.get(path)
    assert first.status_code == 200, first.text
    assert second.status_code == 429, f"{path} must be floored, got {second.status_code}"


# ── AC9: zero path-prefix hardcodes in the rate-limit path ────────────────


@pytest.mark.parametrize("name", ["rate_limit.py", "rate_limit_middleware.py"])
def test_rate_limit_modules_contain_no_path_hardcodes(name: str) -> None:
    src = (_SHARED / name).read_text(encoding="utf-8")
    assert "startswith" not in src, f"path-prefix classification is banned in {name}"
    assert '"/api/v1/"' not in src, f"version-prefix string is banned in {name}"


def test_policy_factory_rejects_unknown_surface() -> None:
    with pytest.raises(ValueError, match="surface"):
        surface_rate_limit("database")


# ── Composition: include_surfaces attaches policy after auth ──────────────


def test_include_surfaces_attaches_policy_right_after_auth() -> None:
    app = FastAPI()
    recorded: list[tuple[str, list]] = []
    original = app.include_router

    def spy(router, *, prefix: str = "", dependencies=None, **kwargs):  # noqa: ANN001, ANN201, ANN003
        recorded.append((prefix, list(dependencies or [])))
        return original(router, prefix=prefix, dependencies=dependencies, **kwargs)

    app.include_router = spy  # type: ignore[method-assign]
    include_surfaces(app)

    assert len(recorded) == len(WEB_ROUTERS) + len(AGENT_ROUTERS) + len(PUBLIC_ROUTERS)
    seen = {"web": 0, "agent": 0, "public": 0}
    for prefix, deps in recorded:
        if not deps:
            seen["public"] += 1
            continue
        first = deps[0].dependency  # auth must run FIRST (principal for the policy)
        if first is web_auth or first is agent_auth:
            surface = "web" if first is web_auth else "agent"
            seen[surface] += 1
            assert len(deps) == 2, f"{prefix}: auth + rate policy expected, got {len(deps)}"
            policy = deps[1].dependency
            assert isinstance(policy, SurfaceRateLimit), policy
            assert policy.surface == surface
        else:
            pytest.fail(f"{prefix}: unexpected leading dependency {first!r}")
    assert seen == {
        "web": len(WEB_ROUTERS),
        "agent": len(AGENT_ROUTERS),
        "public": len(PUBLIC_ROUTERS),
    }


def test_registry_attached_policy_limits_real_agent_route(
    fake_redis: _KeyedRedis, rate_on: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Functional pin: the policy mounted through ``include_surfaces`` limits
    a real AGENT-group route (no floor middleware — the gate alone denies)."""
    monkeypatch.setattr(get_settings(), "rate_limit_agent_max", 1)
    app = FastAPI()
    include_surfaces(app)
    client = TestClient(app)
    statuses = [client.get(MCP_TOOLS).status_code for _ in range(2)]
    assert statuses[0] == 200, f"first call must pass, got {statuses[0]}"
    assert statuses[1] == 429, f"registry-attached policy must deny, got {statuses[1]}"
