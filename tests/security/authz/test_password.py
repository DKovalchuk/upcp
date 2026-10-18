"""Password-change security checks — negative paths only.

The shared seeded admin password must never change, so no success-path
test runs here; lockout is skipped (it would lock the shared account and
no disposable account can be created — /auth/setup is single-use).
"""

from __future__ import annotations

import httpx
import pytest

# Relative: root pyproject pythonpath=["backend"] shadows the top-level
# "tests" package, so absolute tests.security.* imports fail here.
from ..common import PERF_PASSWORD, SECURITY_BASE_URL

BASE = SECURITY_BASE_URL.rstrip("/")

pytestmark = [
    pytest.mark.authz_category("password"),
    pytest.mark.severity("medium"),
]


def test_wrong_current_password_rejected(admin_headers: dict[str, str]) -> None:
    resp = httpx.post(
        f"{BASE}/auth/password/change",
        headers=admin_headers,
        json={
            "current_password": "DefinitelyWrong123!",
            "new_password": "AnotherStr0ng123!",
        },
        timeout=15.0,
    )
    assert resp.status_code == 400, (
        f"wrong current password -> {resp.status_code}, expected 400: {resp.text[:200]}"
    )


def test_weak_new_password_rejected(admin_headers: dict[str, str]) -> None:
    """Schema-level boundary: new password < 8 chars is 422 before any mutation."""
    resp = httpx.post(
        f"{BASE}/auth/password/change",
        headers=admin_headers,
        json={"current_password": PERF_PASSWORD, "new_password": "short"},
        timeout=15.0,
    )
    assert resp.status_code == 422, (
        f"weak new password -> {resp.status_code}, expected 422: {resp.text[:200]}"
    )


def test_password_change_requires_auth() -> None:
    resp = httpx.post(
        f"{BASE}/auth/password/change",
        json={"current_password": "whatever1", "new_password": "whatever2"},
        timeout=15.0,
    )
    assert resp.status_code == 401, (
        f"unauthenticated password change -> {resp.status_code}, expected 401"
    )


@pytest.mark.skip(
    reason="login lockout mutates shared admin@example.com state; no disposable account can "
    "be created (POST /auth/setup is single-use 409) — see README limitations"
)
def test_login_lockout_after_five_failed_attempts() -> None:
    pytest.skip("would lock the shared admin account; not runnable on a shared stack")
