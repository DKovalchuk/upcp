"""JWT access/refresh token security checks (TASK-0142 / SPEC-0024 Phase 4).

Positive: valid JWT accepted. Negative: missing/garbage/expired/wrong-
signature/type-confused tokens rejected; refresh rotation enforced;
logout revokes the refresh token. Finding 2 (nonexistent subject on
domain routes) is closed by TASK-0146; the remaining known gap —
logout denylist (finding 3, TASK-0147) — is a strict=False xfail.
"""

from __future__ import annotations

import httpx
import pytest

# Relative: root pyproject pythonpath=["backend"] shadows the top-level
# "tests" package, so absolute tests.security.* imports fail here.
from ..common import PERF_EMAIL, SECURITY_BASE_URL

BASE = SECURITY_BASE_URL.rstrip("/")
_FAKE_UUID = "00000000-0000-0000-0000-000000000000"

pytestmark = [
    pytest.mark.authz_category("tokens"),
    pytest.mark.severity("medium"),
]


def _me(headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.get(f"{BASE}/auth/me", headers=headers, timeout=15.0)


def _refresh(refresh_token: str) -> httpx.Response:
    return httpx.post(f"{BASE}/auth/refresh", json={"refresh_token": refresh_token}, timeout=15.0)


def _logout(access_token: str, refresh_token: str) -> httpx.Response:
    return httpx.post(
        f"{BASE}/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
        timeout=15.0,
    )


# ── Access token acceptance / rejection ────────────────────────────


def test_valid_jwt_accepted(admin_headers: dict[str, str]) -> None:
    resp = _me(admin_headers)
    assert resp.status_code == 200, f"valid JWT -> {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    assert body.get("email") == PERF_EMAIL
    assert body.get("id")


def test_missing_authorization_header_rejected() -> None:
    resp = _me()
    assert resp.status_code == 401, f"no auth header -> {resp.status_code}, expected 401"
    assert resp.headers.get("www-authenticate") == "Bearer"


@pytest.mark.severity("high")
def test_garbage_bearer_token_rejected() -> None:
    resp = _me({"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401, f"garbage bearer -> {resp.status_code}, expected 401"


@pytest.mark.severity("high")
def test_expired_jwt_rejected(admin_user_id: str, mint) -> None:
    token = mint(admin_user_id, exp_min=-5, iat_min=-10)
    resp = _me({"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401, (
        f"expired but correctly-signed JWT -> {resp.status_code}, expected 401"
    )


@pytest.mark.severity("high")
def test_wrong_signature_jwt_rejected(admin_user_id: str, mint) -> None:
    token = mint(admin_user_id, secret="not-the-real-upcp-secret")
    resp = _me({"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401, f"wrong-signature JWT -> {resp.status_code}, expected 401"


@pytest.mark.severity("high")
def test_refresh_type_jwt_rejected_as_access(admin_user_id: str, mint) -> None:
    token = mint(admin_user_id, typ="refresh")
    resp = _me({"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401, (
        f"type=refresh token used as access -> {resp.status_code}, expected 401"
    )


def test_minted_valid_jwt_accepted(admin_user_id: str, mint) -> None:
    """Also proves the minting secret matches the running stack (UPCP_SECRET_KEY)."""
    token = mint(admin_user_id)
    resp = _me({"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, (
        f"correctly-signed fresh JWT -> {resp.status_code}: {resp.text[:200]}"
    )


@pytest.mark.severity("high")
def test_nonexistent_user_rejected_on_auth_me(mint) -> None:
    token = mint(_FAKE_UUID)
    resp = _me({"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401, (
        f"nonexistent subject on /auth/me -> {resp.status_code}, expected 401"
    )


@pytest.mark.severity("high")
def test_nonexistent_user_rejected_on_domain_endpoint(mint) -> None:
    token = mint(_FAKE_UUID)
    resp = httpx.get(
        f"{BASE}/api/v1/projects", headers={"Authorization": f"Bearer {token}"}, timeout=15.0
    )
    assert resp.status_code == 401, (
        f"nonexistent subject on /api/v1/projects -> {resp.status_code}, expected 401"
    )


# ── Refresh rotation ───────────────────────────────────────────────


def test_refresh_rotation_issues_new_pair(fresh_login: dict) -> None:
    resp = _refresh(fresh_login["refresh_token"])
    assert resp.status_code == 200, f"refresh -> {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    assert body["refresh_token"] != fresh_login["refresh_token"], "refresh must rotate the token"
    used = httpx.get(
        f"{BASE}/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
        timeout=15.0,
    )
    assert used.status_code == 200, f"rotated access token -> {used.status_code}"
    again = _refresh(body["refresh_token"])
    assert again.status_code == 200, (
        f"second hop of the chain -> {again.status_code}: {again.text[:200]}"
    )


def test_reused_refresh_token_rejected(fresh_login: dict) -> None:
    first = _refresh(fresh_login["refresh_token"])
    assert first.status_code == 200, f"first refresh -> {first.status_code}: {first.text[:200]}"
    reuse = _refresh(fresh_login["refresh_token"])
    assert reuse.status_code == 401, (
        f"reused (revoked) refresh -> {reuse.status_code}, expected 401"
    )


def test_garbage_refresh_token_rejected() -> None:
    resp = _refresh("not-a-refresh-token")
    assert resp.status_code == 401, f"garbage refresh -> {resp.status_code}, expected 401"


# ── Logout ─────────────────────────────────────────────────────────


def test_logout_revokes_refresh_token(fresh_login: dict) -> None:
    out = _logout(fresh_login["access_token"], fresh_login["refresh_token"])
    assert out.status_code == 200, f"logout -> {out.status_code}: {out.text[:200]}"
    resp = _refresh(fresh_login["refresh_token"])
    assert resp.status_code == 401, f"refresh after logout -> {resp.status_code}, expected 401"


def test_logout_requires_bearer(fresh_login: dict) -> None:
    resp = httpx.post(
        f"{BASE}/auth/logout",
        json={"refresh_token": fresh_login["refresh_token"]},
        timeout=15.0,
    )
    assert resp.status_code == 401, f"logout without auth -> {resp.status_code}, expected 401"


@pytest.mark.severity("medium")
@pytest.mark.xfail(
    strict=False,
    reason="finding: logout revokes only the refresh token — the access JWT keeps working "
    "until exp (stateless design, 15-minute window, no denylist)",
)
def test_access_token_rejected_after_logout(fresh_login: dict) -> None:
    out = _logout(fresh_login["access_token"], fresh_login["refresh_token"])
    assert out.status_code == 200, f"logout precondition -> {out.status_code}: {out.text[:200]}"
    resp = _me({"Authorization": f"Bearer {fresh_login['access_token']}"})
    assert resp.status_code == 401, f"access token after logout -> {resp.status_code}, expected 401"
