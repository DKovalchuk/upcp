"""Auth-bypass checks: the protected surface rejects anonymous callers.

Parametrized across representative /api/v1 domains (projects, structure,
delivery, quality, reporting, audit, agents, dashboard, search,
notifications, analytics) plus /mcp — without a token everything must be
401; with credentials nothing may be 401/403. Credential per surface
(D5, TASK-0170): web endpoints accept the admin JWT, ``/mcp`` is
agent-key-only and gets a minted ``X-Agent-Token``. Documented-public
paths must stay reachable without credentials.
"""

from __future__ import annotations

import httpx
import pytest

# Relative: root pyproject pythonpath=["backend"] shadows the top-level
# "tests" package, so absolute tests.security.* imports fail here.
from ..common import SECURITY_BASE_URL

BASE = SECURITY_BASE_URL.rstrip("/")
_FAKE_UUID = "00000000-0000-0000-0000-000000000000"
_MCP_PROBE_AGENT = "sec-authz-mcp-probe"

pytestmark = [
    pytest.mark.authz_category("auth-bypass"),
    pytest.mark.severity("high"),
]

# (id, method, path) — with-token statuses verified: 200/404/422 (never 401/403)
PROTECTED_ENDPOINTS = [
    ("projects", "GET", "/api/v1/projects"),
    ("structure-component", "GET", f"/api/v1/components/{_FAKE_UUID}"),
    ("delivery-feature-tasks", "GET", f"/api/v1/features/{_FAKE_UUID}/tasks"),
    ("quality-dod-items", "GET", f"/api/v1/dod-items/{_FAKE_UUID}"),
    ("reporting-reports", "GET", f"/api/v1/reports/{_FAKE_UUID}"),
    ("audit-export", "GET", "/api/v1/audit/export"),
    ("agents", "GET", "/api/v1/agents"),
    ("dashboard-stats", "GET", "/api/v1/dashboard/stats"),
    ("search", "GET", "/api/v1/search?q=test"),
    ("notifications", "GET", "/api/v1/notifications"),
    ("analytics-velocity", "GET", "/api/v1/analytics/velocity"),
    ("mcp-tools", "GET", "/mcp/tools"),
]

_PARAM = pytest.mark.parametrize(
    ("name", "method", "path"),
    PROTECTED_ENDPOINTS,
    ids=[entry[0] for entry in PROTECTED_ENDPOINTS],
)


@pytest.fixture(scope="module")
def agent_headers(admin_headers: dict[str, str]) -> dict[str, str]:
    """D5 (TASK-0170): ``/mcp`` accepts agent keys only — mint a probe token.

    Find-or-create a probe agent (test_rbac precedent), then mint one token
    per run (the raw value is returned exactly once by the API).
    """
    resp = httpx.get(
        f"{BASE}/api/v1/agents",
        headers=admin_headers,
        params={"limit": 200},
        timeout=15.0,
    )
    assert resp.status_code == 200, f"list agents -> {resp.status_code}: {resp.text[:200]}"
    agent_id = next(
        (i["id"] for i in resp.json().get("items", []) if i.get("name") == _MCP_PROBE_AGENT),
        None,
    )
    if agent_id is None:
        resp = httpx.post(
            f"{BASE}/api/v1/agents",
            headers=admin_headers,
            json={"name": _MCP_PROBE_AGENT, "description": "TASK-0170 D5 /mcp caller probe"},
            timeout=15.0,
        )
        assert resp.status_code == 201, (
            f"create probe agent -> {resp.status_code}: {resp.text[:200]}"
        )
        agent_id = str(resp.json()["id"])
    resp = httpx.post(
        f"{BASE}/api/v1/agents/{agent_id}/tokens",
        headers=admin_headers,
        json={"name": "authz-mcp-probe"},
        timeout=15.0,
    )
    assert resp.status_code == 201, f"create token -> {resp.status_code}: {resp.text[:200]}"
    return {"X-Agent-Token": resp.json()["token"]}


@_PARAM
def test_anonymous_request_rejected(name: str, method: str, path: str) -> None:
    resp = httpx.request(method, f"{BASE}{path}", timeout=15.0)
    assert resp.status_code == 401, (
        f"{method} {path} without token -> {resp.status_code}, expected 401"
    )


@_PARAM
def test_valid_token_accepted(
    name: str,
    method: str,
    path: str,
    admin_headers: dict[str, str],
    agent_headers: dict[str, str],
) -> None:
    # D5 (TASK-0170): agent surface is agent-key-only; web surface keeps JWT.
    headers = agent_headers if name == "mcp-tools" else admin_headers
    resp = httpx.request(method, f"{BASE}{path}", headers=headers, timeout=15.0)
    assert resp.status_code not in (401, 403), (
        f"{method} {path} with valid credentials -> {resp.status_code}, auth should pass"
    )


@pytest.mark.parametrize(
    "auth_value",
    ["Bearer", "Bearer garbage", "Basic dXNlcjpwdw"],
    ids=["bare-scheme", "garbage-bearer", "basic-scheme"],
)
def test_malformed_authorization_rejected(auth_value: str) -> None:
    resp = httpx.get(f"{BASE}/auth/me", headers={"Authorization": auth_value}, timeout=15.0)
    assert resp.status_code == 401, (
        f"Authorization: {auth_value!r} -> {resp.status_code}, expected 401"
    )


def test_unknown_agent_token_rejected() -> None:
    resp = httpx.get(f"{BASE}/api/v1/projects", headers={"X-Agent-Token": "garbage"}, timeout=15.0)
    assert resp.status_code == 401, f"garbage X-Agent-Token -> {resp.status_code}, expected 401"


@pytest.mark.authz_category("boundary")
@pytest.mark.severity("medium")
@pytest.mark.parametrize("path", ["/health", "/api/v1/health"], ids=["root-health", "api-health"])
def test_public_health_without_token(path: str) -> None:
    resp = httpx.get(f"{BASE}{path}", timeout=15.0)
    assert resp.status_code == 200, f"documented-public {path} -> {resp.status_code}, expected 200"
