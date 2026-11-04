"""RBAC checks — agent-token ownership (superuser/owner gate) and
role-enforcement on project mutations (strict since TASK-0145).

Second identity: the stack seeds non-superuser users (seeder.py) and
POST /auth/setup is single-use (409), so member checks reuse a seeded
user discovered read-only via member_identity; JWTs for it are minted
with the test-stack secret (same technique as the expired-token probe).
"""

from __future__ import annotations

import httpx
import pytest

# Relative: root pyproject pythonpath=["backend"] shadows the top-level
# "tests" package, so absolute tests.security.* imports fail here.
from ..common import SECURITY_BASE_URL

BASE = SECURITY_BASE_URL.rstrip("/")
_FAKE_UUID = "00000000-0000-0000-0000-000000000000"
_PROBE_AGENT_NAME = "sec-authz-probe"

pytestmark = [
    pytest.mark.authz_category("rbac"),
    pytest.mark.severity("high"),
]


@pytest.fixture(scope="module")
def probe_agent(admin_headers: dict[str, str]) -> str:
    """Reuse the suite's probe agent across runs to limit junk rows."""
    resp = httpx.get(
        f"{BASE}/api/v1/agents",
        headers=admin_headers,
        params={"limit": 200},
        timeout=15.0,
    )
    assert resp.status_code == 200, f"list agents -> {resp.status_code}: {resp.text[:200]}"
    for item in resp.json().get("items", []):
        if item.get("name") == _PROBE_AGENT_NAME:
            return str(item["id"])
    resp = httpx.post(
        f"{BASE}/api/v1/agents",
        headers=admin_headers,
        json={"name": _PROBE_AGENT_NAME, "description": "TASK-0142 authz suite probe (reused)"},
        timeout=15.0,
    )
    assert resp.status_code == 201, f"create probe agent -> {resp.status_code}: {resp.text[:200]}"
    return str(resp.json()["id"])


@pytest.fixture(scope="module")
def owner_token(probe_agent: str, admin_headers: dict[str, str]) -> dict:
    """A token on the probe agent owned by the superuser admin."""
    resp = httpx.post(
        f"{BASE}/api/v1/agents/{probe_agent}/tokens",
        headers=admin_headers,
        json={"name": "authz-probe"},
        timeout=15.0,
    )
    assert resp.status_code == 201, f"create token -> {resp.status_code}: {resp.text[:200]}"
    return resp.json()


def test_owner_can_create_agent_token(owner_token: dict) -> None:
    assert owner_token.get("id"), "created token must carry an id"
    assert owner_token.get("token"), "raw token must be returned exactly once"


def test_member_cannot_create_agent_token(probe_agent: str, member_headers: dict[str, str]) -> None:
    resp = httpx.post(
        f"{BASE}/api/v1/agents/{probe_agent}/tokens",
        headers=member_headers,
        json={"name": "authz-probe"},
        timeout=15.0,
    )
    assert resp.status_code == 403, (
        f"non-owner non-superuser token create -> {resp.status_code}, expected 403: {resp.text[:200]}"
    )


def test_member_cannot_revoke_agent_token(
    owner_token: dict, member_headers: dict[str, str]
) -> None:
    resp = httpx.post(
        f"{BASE}/api/v1/agent-tokens/{owner_token['id']}/revoke",
        headers=member_headers,
        timeout=15.0,
    )
    assert resp.status_code == 403, (
        f"non-owner non-superuser revoke -> {resp.status_code}, expected 403: {resp.text[:200]}"
    )


def test_owner_can_revoke_agent_token(owner_token: dict, admin_headers: dict[str, str]) -> None:
    resp = httpx.post(
        f"{BASE}/api/v1/agent-tokens/{owner_token['id']}/revoke",
        headers=admin_headers,
        timeout=15.0,
    )
    assert resp.status_code == 200, f"owner revoke -> {resp.status_code}: {resp.text[:200]}"


def test_revoked_agent_token_rejected(probe_agent: str, admin_headers: dict[str, str]) -> None:
    created = httpx.post(
        f"{BASE}/api/v1/agents/{probe_agent}/tokens",
        headers=admin_headers,
        # FIX-1 (TASK-0175): scopeless keys default to deny-all —
        # GET /api/v1/agent/me is gated with agent:self.
        json={"name": "authz-lifecycle", "scopes": ["agent:self"]},
        timeout=15.0,
    )
    assert created.status_code == 201, f"create lifecycle token -> {created.status_code}"
    raw = created.json()["token"]
    active = httpx.get(f"{BASE}/api/v1/agent/me", headers={"X-Agent-Token": raw}, timeout=15.0)
    assert active.status_code == 200, (
        f"fresh agent token auth -> {active.status_code}: {active.text[:200]}"
    )
    revoked = httpx.post(
        f"{BASE}/api/v1/agent-tokens/{created.json()['id']}/revoke",
        headers=admin_headers,
        timeout=15.0,
    )
    assert revoked.status_code == 200, f"revoke -> {revoked.status_code}"
    after = httpx.get(f"{BASE}/api/v1/agent/me", headers={"X-Agent-Token": raw}, timeout=15.0)
    assert after.status_code == 401, f"revoked agent token -> {after.status_code}, expected 401"


def test_member_can_read_agent_list(member_headers: dict[str, str]) -> None:
    """Positive control: member JWT is valid and read access to agents is allowed."""
    resp = httpx.get(f"{BASE}/api/v1/agents", headers=member_headers, timeout=15.0)
    assert resp.status_code == 200, (
        f"member GET /api/v1/agents -> {resp.status_code}: {resp.text[:200]}"
    )


def test_member_update_project_enforces_role(member_headers: dict[str, str]) -> None:
    """Finding 1 closed (TASK-0145): require_permission gate answers 403
    before resource lookup — was strict=False xfail while no authorization
    layer ran for domain routes."""
    resp = httpx.patch(
        f"{BASE}/api/v1/projects/{_FAKE_UUID}",
        headers=member_headers,
        json={"name": "nope"},
        timeout=15.0,
    )
    assert resp.status_code == 403, (
        f"Member patching a project -> {resp.status_code}, RBAC intent requires 403"
    )
