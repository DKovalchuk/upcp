"""Shared helpers for the security suite (TASK-0142 / SPEC-0024 Phase 4).

Conventions mirror tests/chaos/engine.py: target URL via env with a
localhost default, auth via a cached Bearer JWT from a real login.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

# Live test-stack backend (docker-compose.test.yml binds 127.0.0.1:38082)
SECURITY_BASE_URL = os.getenv("SECURITY_BASE_URL", "http://localhost:38082")
PERF_EMAIL = os.getenv("PERF_EMAIL", "admin@example.com")
PERF_PASSWORD = os.getenv("PERF_PASSWORD", "TestAdmin123!")

_auth_cache: dict[str, str] | None = None


def login(base_url: str | None = None) -> dict[str, str]:
    """Authenticate against /auth/login and return headers with the JWT."""
    global _auth_cache
    if _auth_cache is not None:
        return _auth_cache
    base = (base_url or SECURITY_BASE_URL).rstrip("/")
    resp = httpx.post(
        f"{base}/auth/login",
        json={"email": PERF_EMAIL, "password": PERF_PASSWORD},
        timeout=15.0,
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    _auth_cache = {"Authorization": f"Bearer {token}"}
    return _auth_cache


def health_ok(base_url: str | None = None) -> bool:
    """Pre-flight: target must be up before any suite runs."""
    base = (base_url or SECURITY_BASE_URL).rstrip("/")
    try:
        r = httpx.get(f"{base}/health", timeout=5.0)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


def check(
    name: str,
    category: str,
    ok: bool,
    *,
    expected: str = "",
    actual: str = "",
    detail: str = "",
    severity: str = "",
) -> dict[str, Any]:
    """Build one check record in the shared result schema."""
    return {
        "name": name,
        "category": category,
        "status": "pass" if ok else "fail",
        "expected": expected,
        "actual": actual,
        "detail": detail,
        "severity": severity,  # finding severity when status=fail
    }


def finding(check_rec: dict[str, Any]) -> dict[str, Any]:
    """Extract a finding (actionable vulnerability report) from a failed check."""
    return {
        "severity": check_rec.get("severity") or "medium",
        "title": check_rec["name"],
        "category": check_rec["category"],
        "detail": check_rec.get("detail") or check_rec.get("actual", ""),
    }


def summarize(
    suite: str, target: str, checks: list[dict[str, Any]], **extra: Any
) -> dict[str, Any]:
    """Assemble the shared result document written to results/<suite>_<ts>.json."""
    failed = [c for c in checks if c["status"] == "fail"]
    return {
        "schema": "upcp-security-result/v1",
        "suite": suite,
        "target": target,
        "checks": checks,
        "findings": [finding(c) for c in failed],
        "summary": {
            "total": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
        },
        **extra,
    }
