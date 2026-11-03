"""AC1 default-deny enumeration — SPEC-0028 AC1 / finding 9 / TASK-0169.

Mechanism-agnostic regression net (the missed scenario class): iterate
EVERY route of the web and agent surface groups as mounted on the real
production app and request each one WITHOUT credentials — no route may
answer 2xx (401 expected). PUBLIC group routes are skipped; their
unauthenticated 200s are asserted separately (AC2).

Characterization status: written GREEN under ``AuthMiddleware`` — its
regression value materializes in TASK-0170, which removes the middleware:
the web group is then guarded by the ``web_auth`` blanket and this test is
what catches a route that silently loses its guard.

Mount parity: the hermetic suite runs ``UPCP_DISABLE_AUTH=true`` and
``main.py`` mounts ``AuthMiddleware`` at IMPORT time only when the flag is
false — so this module re-runs that production decision once inside an
auth-enabled env window before the first import of ``app.main`` (the env
is restored immediately; after TASK-0170 the window is inert because
protection moves to per-request dependencies).
"""

from __future__ import annotations

import os
import re
from unittest.mock import patch

import pytest
from app.api.registry import AGENT_ROUTERS, WEB_ROUTERS
from app.shared.config import get_settings
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

_ORIG_DISABLE_AUTH = os.environ.get("UPCP_DISABLE_AUTH")
os.environ["UPCP_DISABLE_AUTH"] = "false"
get_settings.cache_clear()

from app.main import app  # noqa: E402 — must run inside the auth-enabled window

if _ORIG_DISABLE_AUTH is None:
    os.environ.pop("UPCP_DISABLE_AUTH", None)
else:
    os.environ["UPCP_DISABLE_AUTH"] = _ORIG_DISABLE_AUTH
get_settings.cache_clear()

# No lifespan (precedent: tests/test_health.py) — the guards are import/route
# level; raise_server_exceptions=False so a fail-open that 500s inside a
# handler shows up as a reportable failure instead of aborting the loop.
client = TestClient(app, raise_server_exceptions=False)

_DUMMY = "00000000-0000-0000-0000-000000000000"


@pytest.fixture()
def auth_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auth deps evaluate the flag per request — turn the guard ON for AC1.

    Pre-TASK-0170 this is redundant for the middleware (mounted already)
    but harmless; post-TASK-0170 the dependencies are what deny.
    """
    monkeypatch.setattr(get_settings(), "disable_auth", False)


def _surface_targets() -> list[tuple[str, str, str]]:
    """``(surface, method, path)`` for every declared route of web + agent."""
    targets: list[tuple[str, str, str]] = []
    for surface, group in (("web", WEB_ROUTERS), ("agent", AGENT_ROUTERS)):
        for router, prefix in group:
            for route in router.routes:
                if not isinstance(route, APIRoute):
                    continue
                path = prefix + re.sub(r"\{[^}]+\}", _DUMMY, route.path)
                for method in sorted(route.methods):
                    targets.append((surface, method, path))
    return targets


def test_every_web_and_agent_route_denies_unauthenticated_requests(
    auth_enabled: None,
) -> None:
    """AC1: enumerating web + agent routes without credentials → never 2xx."""
    targets = _surface_targets()
    assert targets, "registry must expose both surface groups"
    assert {surface for surface, _, _ in targets} == {"web", "agent"}

    failures: list[str] = []
    seen: set[str] = set()
    for surface, method, path in targets:
        seen.add(path)
        resp = client.request(method, path)
        if resp.status_code != 401:
            failures.append(f"{method} {path} [{surface}] -> {resp.status_code}")

    assert not failures, (
        "unauthenticated requests must be denied 401 on every web/agent route "
        f"({len(targets)} targets): {failures}"
    )


def test_public_health_routes_stay_reachable_unauthenticated(auth_enabled: None) -> None:
    """AC2: declared public routes keep their normal 200 without credentials."""
    with (
        patch(
            "app.shared.redis.check_redis_health",
            return_value={"status": "ok", "service": "redis"},
        ),
        patch(
            "app.main.check_db_health",
            return_value={"status": "ok", "latency_ms": 1.0},
        ),
    ):
        for path in ("/health", "/api/v1/health"):
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} -> {resp.status_code}: {resp.text[:200]}"
