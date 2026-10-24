"""Security tests for dashboard/analytics API — TASK-0128 Part E (E1-E9).

E1-E4: 401 without token / with invalid token on all four dashboard endpoints.
E5:    project_id SQL injection payloads are safely filtered — 200/422 only,
       never 500, no row leak, schema intact.
E6-E7: XSS payloads round-trip raw in JSON responses served as
       application/json. Backend has no server-rendered HTML path that
       reflects stored data (only OpenAPI /docs), so the meaningful backend
       boundary is: application/json content type + valid JSON structure +
       no mangling of stored strings. Frontend escaping is covered by Part B.
E8:    /api/v1/dashboard/stats returns 429 after a (low) threshold.
E9:    CORS: only origins from settings.cors_origins_list get
       Access-Control-Allow-Origin.
"""

from uuid import uuid4

import app.audit.models  # noqa: F401 — register audit tables (stats queries them)
import pytest
from app.api.v1.analytics import router as analytics_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.structure import router as structure_router  # noqa: F401
from app.delivery.models import Feature, Task
from app.identity.middleware import AuthMiddleware
from app.identity.token_service import TokenService
from app.projects.models import Project
from app.shared import rate_limit as rate_limit_mod
from app.shared.config import Settings
from app.shared.rate_limit_middleware import RateLimitMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.conftest import _TestSession, make_test_app

# ── Helpers ────────────────────────────────────────────────────

_PROTECTED_ENDPOINTS = [
    "/api/v1/dashboard/stats",
    "/api/v1/analytics/velocity",
    "/api/v1/dashboard/attention",
    "/api/v1/portfolio/overview",
]
_ENDPOINT_IDS = ["E1-stats", "E2-velocity", "E3-attention", "E4-portfolio"]

SQLI_PAYLOADS = [
    "' OR 1=1--",
    '" OR ""="',
    "1; DROP TABLE projects;--",
    "'; DROP TABLE tasks;--",
]
SQLI_ENDPOINTS = [
    "/api/v1/dashboard/stats",
    "/api/v1/dashboard/attention",
    "/api/v1/analytics/velocity",
]


def _open_client() -> TestClient:
    """App with conftest defaults (auth/rate-limit middleware off)."""
    app = make_test_app(
        projects_router, structure_router, delivery_router, dashboard_router, analytics_router
    )
    return TestClient(app)


def _seed_project(client: TestClient, *, status: str = "done", title: str = "Seeded") -> dict:
    """Create project → feature → task with the given status/title via the API."""
    project = client.post("/api/v1/projects", json={"name": "E-Seed"}).json()
    feature = client.post(
        f"/api/v1/projects/{project['id']}/features",
        json={"name": "E-Feature", "slug": "e-seed"},
    ).json()
    task = client.post(
        f"/api/v1/features/{feature['id']}/tasks",
        json={"title": title, "status": status},
    ).json()
    return {"project": project, "feature": feature, "task": task}


@pytest.fixture()
def client() -> TestClient:
    return _open_client()


# ── E1-E4: endpoints require auth ─────────────────────────────


@pytest.fixture()
def auth_client() -> TestClient:
    app = make_test_app(dashboard_router, analytics_router)
    app.add_middleware(AuthMiddleware)
    return TestClient(app)


@pytest.mark.parametrize("endpoint", _PROTECTED_ENDPOINTS, ids=_ENDPOINT_IDS)
def test_e1_e4_missing_token_returns_401(auth_client: TestClient, endpoint: str) -> None:
    """No Authorization header → 401 with WWW-Authenticate."""
    resp = auth_client.get(endpoint)
    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"
    assert "detail" in resp.json()


@pytest.mark.parametrize("endpoint", _PROTECTED_ENDPOINTS, ids=_ENDPOINT_IDS)
def test_e1_e4_invalid_token_returns_401(auth_client: TestClient, endpoint: str) -> None:
    """Malformed JWT → 401 (guard rejects before hitting the route)."""
    resp = auth_client.get(endpoint, headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert resp.status_code == 401
    assert "detail" in resp.json()


def test_valid_token_reaches_dashboard_stats(seed_subject) -> None:
    """Control: 401 comes from the auth guard — a valid JWT for a live subject → 200."""
    ts = TokenService()
    app = make_test_app(dashboard_router, analytics_router)
    app.add_middleware(AuthMiddleware, token_service=ts)
    client = TestClient(app)
    seed_subject("user-123")
    token = ts.create_access_token("user-123")
    resp = client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


# ── E5: project_id SQL injection ──────────────────────────────


@pytest.mark.parametrize(
    "payload",
    SQLI_PAYLOADS,
    ids=["quote-or", "dquote", "drop-projects", "drop-tasks"],
)
@pytest.mark.parametrize("endpoint", SQLI_ENDPOINTS, ids=["stats", "attention", "velocity"])
def test_e5_project_id_sql_injection_never_500(
    client: TestClient, endpoint: str, payload: str
) -> None:
    """Injection payloads are parameter-bound: 200 (filtered) or 422, JSON, never 500."""
    resp = client.get(endpoint, params={"project_id": payload})
    assert resp.status_code in (200, 422)
    assert resp.headers["content-type"].startswith("application/json")


def test_e5_url_encoded_injection_in_raw_query(client: TestClient) -> None:
    """URL-encoded payload decodes server-side to ' OR 1=1-- and is still filtered."""
    _seed_project(client)
    resp = client.get("/api/v1/dashboard/stats?project_id=%27%20OR%201%3D1--")
    assert resp.status_code in (200, 422)
    assert resp.json()["task_counts_by_status"]["done"] == 0


def test_e5_stats_injection_returns_no_extra_rows(client: TestClient) -> None:
    """Injection must behave exactly like a non-matching id — no bypassed filter."""
    _seed_project(client)
    inj = client.get("/api/v1/dashboard/stats", params={"project_id": "' OR 1=1--"})
    ctrl = client.get("/api/v1/dashboard/stats", params={"project_id": str(uuid4())})
    assert inj.status_code == ctrl.status_code == 200
    inj_body, ctrl_body = inj.json(), ctrl.json()
    for key in ("task_counts_by_status", "done_this_week", "blocked_count", "claimed_count"):
        assert inj_body[key] == ctrl_body[key]
    # If the filter were bypassed, the seeded done task would leak through:
    assert inj_body["task_counts_by_status"]["done"] == 0


def test_e5_attention_injection_returns_no_rows(client: TestClient) -> None:
    """Injection on attention must not surface another project's blocked tasks."""
    _seed_project(client, status="blocked")
    unscoped = client.get("/api/v1/dashboard/attention")
    assert len(unscoped.json()["blocked_tasks"]) == 1  # sanity: data exists

    inj = client.get("/api/v1/dashboard/attention", params={"project_id": "' OR 1=1--"})
    assert inj.status_code == 200
    assert inj.json()["blocked_tasks"] == []


def test_e5_tables_intact_after_sql_injection(client: TestClient) -> None:
    """DROP TABLE payloads leave schema and data untouched; endpoints keep working."""
    _seed_project(client)
    for endpoint in SQLI_ENDPOINTS:
        for payload in SQLI_PAYLOADS:
            resp = client.get(endpoint, params={"project_id": payload})
            assert resp.status_code in (200, 422)

    session = _TestSession()
    try:
        rows = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = {row[0] for row in rows}
    finally:
        session.close()
    expected = {Project.__table__.name, Feature.__table__.name, Task.__table__.name}
    assert expected <= tables

    stats = client.get("/api/v1/dashboard/stats")
    assert stats.status_code == 200
    assert stats.json()["project_count"] == 1


# ── E6/E7: XSS payloads served as JSON, raw and un-mangled ────


def test_e6_xss_project_name_json_boundary(client: TestClient) -> None:
    """XSS project name: application/json content type, valid JSON, raw round-trip."""
    xss = "<script>alert('xss')</script>"
    created = client.post("/api/v1/projects", json={"name": xss})
    assert created.status_code in (200, 201)
    assert created.headers["content-type"].startswith("application/json")
    assert created.json()["name"] == xss

    stats = client.get("/api/v1/dashboard/stats")
    assert stats.headers["content-type"].startswith("application/json")
    assert "text/html" not in stats.headers["content-type"]
    body = stats.json()
    assert isinstance(body, dict)  # valid JSON structure
    assert xss in [p["name"] for p in body["recent_projects"]]
    assert "&lt;script&gt;" not in stats.text  # raw, not HTML-escaped

    portfolio = client.get("/api/v1/portfolio/overview")
    assert portfolio.headers["content-type"].startswith("application/json")
    assert isinstance(portfolio.json(), dict)


def test_e7_xss_task_title_json_boundary(client: TestClient) -> None:
    """XSS task title: served raw as JSON in delivery + attention, never text/html."""
    xss = "<img src=x onerror=alert(1)>"
    seeded = _seed_project(client, status="blocked", title=xss)

    tasks = client.get(f"/api/v1/features/{seeded['feature']['id']}/tasks")
    assert tasks.headers["content-type"].startswith("application/json")
    assert tasks.json()["items"][0]["title"] == xss

    attention = client.get("/api/v1/dashboard/attention")
    assert attention.headers["content-type"].startswith("application/json")
    blocked = attention.json()["blocked_tasks"]
    assert len(blocked) == 1
    assert blocked[0]["title"] == xss
    assert "&lt;img" not in attention.text


# ── E8: rate limiting on stats endpoint ───────────────────────


class _FakePipe:
    """Minimal redis pipeline: counts requests, returns zcard = prior count."""

    def __init__(self, state: dict) -> None:
        self._state = state

    def zremrangebyscore(self, *args: object, **kwargs: object) -> "_FakePipe":
        return self

    def zcard(self, *args: object, **kwargs: object) -> "_FakePipe":
        return self

    def zadd(self, *args: object, **kwargs: object) -> "_FakePipe":
        return self

    def expire(self, *args: object, **kwargs: object) -> "_FakePipe":
        return self

    def execute(self) -> list[object]:
        seen = self._state["count"]
        self._state["count"] = seen + 1
        return [None, seen, True, True]


class _FakeRedis:
    def __init__(self) -> None:
        self._state = {"count": 0}

    def pipeline(self, transaction: bool = True) -> _FakePipe:  # noqa: ARG002
        return _FakePipe(self._state)

    def zrem(self, *args: object, **kwargs: object) -> None:
        return None


def test_e8_stats_rate_limit_429_after_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    """429 after low threshold (3/min) on /api/v1/dashboard/stats.

    UPCP_DISABLE_RATE_LIMIT only gates registration in main.py, so the
    middleware is registered explicitly here with a low per-route limit.
    """
    fake_redis = _FakeRedis()
    monkeypatch.setattr(rate_limit_mod, "get_redis_client", lambda: fake_redis)
    monkeypatch.setitem(rate_limit_mod.DEFAULT_LIMITS, "default", (3, 60))

    app = make_test_app(dashboard_router)
    app.add_middleware(RateLimitMiddleware)
    client = TestClient(app)

    allowed = [client.get("/api/v1/dashboard/stats") for _ in range(3)]
    assert [r.status_code for r in allowed] == [200, 200, 200]
    assert allowed[0].headers["X-RateLimit-Limit"] == "3"

    blocked = client.get("/api/v1/dashboard/stats")
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "60"
    assert blocked.json() == {"detail": "Too many requests", "retry_after": 60}


# ── E9: CORS — only allowed origins ───────────────────────────

_ALLOWED_ORIGINS = "https://app.example.com,https://admin.example.com"


def _cors_app(settings: Settings) -> FastAPI:
    """Mirror main.py CORS wiring with the given settings."""
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, "cors_origins_list", []),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=getattr(settings, "cors_allow_headers_list", []),
    )

    @app.get("/api/v1/ping")
    def ping() -> dict[str, bool]:
        return {"ok": True}

    return app


@pytest.fixture()
def cors_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("UPCP_CORS_ORIGINS", _ALLOWED_ORIGINS)
    return TestClient(_cors_app(Settings()))


def test_e9_allowed_origin_simple_request_has_acao(cors_client: TestClient) -> None:
    resp = cors_client.get("/api/v1/ping", headers={"Origin": "https://app.example.com"})
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "https://app.example.com"
    assert resp.headers["access-control-allow-credentials"] == "true"


def test_e9_disallowed_origin_simple_request_no_acao(cors_client: TestClient) -> None:
    resp = cors_client.get("/api/v1/ping", headers={"Origin": "https://evil.example.com"})
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers


def test_e9_allowed_origin_preflight_has_acao(cors_client: TestClient) -> None:
    resp = cors_client.options(
        "/api/v1/ping",
        headers={"Origin": "https://admin.example.com", "Access-Control-Request-Method": "GET"},
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "https://admin.example.com"


def test_e9_disallowed_origin_preflight_no_acao(cors_client: TestClient) -> None:
    resp = cors_client.options(
        "/api/v1/ping",
        headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in resp.headers
