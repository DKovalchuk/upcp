"""Pytest plugin + shared fixtures for the authz security suite.

TASK-0142 / SPEC-0024 Phase 4 — integration checks against the LIVE test
stack (auth ON), unlike backend/tests unit suite (UPCP_DISABLE_AUTH=true).

At session finish the plugin writes ONE JSON document
(schema "upcp-security-result/v1") to $SECURITY_RESULT_OUT when set.
One collected test == one check:

* passed test          -> status "pass"
* failed test          -> status "fail", detail = assertion message
* xfail (strict=False) -> status "fail", detail = "xfail (known finding): …"
                          known gaps surface as findings; pytest stays green
* skipped test         -> entry in top-level "skipped" (not a pass/fail check)

Exit-code semantics remain pytest's own: 0 green / 1 failures.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
import pytest

# Relative imports on purpose: root pyproject sets pythonpath=["backend"], and
# backend/tests is a regular package that shadows "tests" on sys.path, so
# absolute "tests.security.common" imports fail. pytest imports this package
# as security.authz.* (tests/ has no __init__.py) and adds tests/ to sys.path.
from ..common import (
    PERF_EMAIL,
    PERF_PASSWORD,
    SECURITY_BASE_URL,
    check,
    health_ok,
    login,
    summarize,
)
from .minting import mint_access

BASE = SECURITY_BASE_URL.rstrip("/")
_SUITE_ROOT = "tests/security/authz"
_DEFAULT_SEVERITY = {"auth-bypass": "high", "rbac": "high"}
_CATEGORY_BY_FILE = {
    "test_authz_bypass.py": "auth-bypass",
    "test_rbac.py": "rbac",
    "test_password.py": "password",
    "test_tokens.py": "tokens",
}

_ITEMS: dict[str, Any] = {}
_REPORTS: dict[str, list[Any]] = {}


# ── Result-recording hooks ─────────────────────────────────────────


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "authz_category(name): result category for a security check")
    config.addinivalue_line("markers", "severity(level): finding severity when this check fails")


def pytest_collection_modifyitems(config: pytest.Config, items: list[Any]) -> None:  # noqa: ARG001
    for item in items:
        _ITEMS[item.nodeid] = item


def pytest_runtest_logreport(report: Any) -> None:
    _REPORTS.setdefault(report.nodeid, []).append(report)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:  # noqa: ARG001
    out = os.getenv("SECURITY_RESULT_OUT", "").strip()
    if not out:
        return
    checks, skipped, xfailed = _build_checks()
    doc = summarize(
        suite="authz",
        target=BASE,
        checks=checks,
        skipped=skipped,
        xfailed=xfailed,
        notes=[
            "xfail tests are recorded as failed checks (known findings); exit code stays pytest's"
        ],
    )
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    s = doc["summary"]
    print(
        f"\n[authz] result -> {path} | total={s['total']} passed={s['passed']} "
        f"failed={s['failed']} skipped={len(skipped)} xfail={len(xfailed)}"
    )


def _in_suite(nodeid: str) -> bool:
    n = nodeid.replace("\\", "/")
    return n.startswith(_SUITE_ROOT + "/") or "/authz/" in n


def _skip_reason(report: Any) -> str:
    longrepr = report.longrepr
    if isinstance(longrepr, tuple) and len(longrepr) >= 3:
        return str(longrepr[2]).strip()
    return str(longrepr).strip()[:300]


def _failure_detail(report: Any) -> str:
    try:
        text = report.longreprtext
    except Exception:  # pragma: no cover - defensive
        text = str(report.longrepr)
    return text.strip()[:800] or "test failed without an assertion message"


def _classify(nodeid: str) -> tuple[str, str]:
    """Map pytest phases to (pass | fail | xfail | skip, detail)."""
    phases = {r.when: r for r in _REPORTS.get(nodeid, [])}
    setup, call, teardown = phases.get("setup"), phases.get("call"), phases.get("teardown")
    if call is not None:
        wasxfail = getattr(call, "wasxfail", None)
        if wasxfail is not None:
            if call.outcome == "skipped":
                return "xfail", str(wasxfail)
            return "pass", f"xpassed (known gap may be fixed): {wasxfail}"
    for phase in (setup, call):
        if phase is not None and phase.outcome == "skipped":
            return "skip", _skip_reason(phase)
    for phase in (setup, call, teardown):
        if phase is not None and phase.outcome == "failed":
            return "fail", _failure_detail(phase)
    return "pass", ""


def _marker_arg(item: Any, name: str) -> str:
    if item is None:
        return ""
    marker = item.get_closest_marker(name)
    if marker is not None and marker.args:
        return str(marker.args[0])
    return ""


def _guess_category(nodeid: str) -> str:
    filename = nodeid.replace("\\", "/").rsplit("/", 1)[-1].split("::", 1)[0]
    return _CATEGORY_BY_FILE.get(filename, "general")


def _record(item: Any, nodeid: str, category: str, *, ok: bool, detail: str) -> dict[str, Any]:
    severity = ""
    if not ok:
        severity = _marker_arg(item, "severity") or _DEFAULT_SEVERITY.get(category, "medium")
    return check(nodeid, category, ok, detail=detail, severity=severity)


def _build_checks() -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    checks: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    xfailed: list[dict[str, str]] = []
    for nodeid in sorted(_REPORTS):
        if not _in_suite(nodeid):
            continue
        item = _ITEMS.get(nodeid)
        state, detail = _classify(nodeid)
        if state == "skip":
            skipped.append({"name": nodeid, "reason": detail})
            continue
        category = _marker_arg(item, "authz_category") or _guess_category(nodeid)
        if state == "xfail":
            xfailed.append({"name": nodeid, "reason": detail})
            checks.append(
                _record(item, nodeid, category, ok=False, detail=f"xfail (known finding): {detail}")
            )
        elif state == "fail":
            checks.append(_record(item, nodeid, category, ok=False, detail=detail))
        else:
            checks.append(_record(item, nodeid, category, ok=True, detail=detail))
    return checks, skipped, xfailed


# ── Shared fixtures ────────────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def _target_up() -> None:
    """Refuse to report an untested pass: a dead target must fail the run."""
    if not health_ok():
        pytest.fail(
            f"security target {BASE} is not healthy — authz suite cannot run", pytrace=False
        )


@pytest.fixture(scope="session")
def jwt_secret() -> str:
    return os.getenv("UPCP_SECRET_KEY", "test_secret_for_quality_gate_only")


@pytest.fixture(scope="session")
def admin_headers() -> dict[str, str]:
    """Cached Bearer headers for the seeded admin (tests.security.common.login)."""
    return login()


@pytest.fixture(scope="session")
def admin_user_id(admin_headers: dict[str, str]) -> str:
    resp = httpx.get(f"{BASE}/auth/me", headers=admin_headers, timeout=15.0)
    assert resp.status_code == 200, f"/auth/me -> {resp.status_code}: {resp.text[:200]}"
    return str(resp.json()["id"])


@pytest.fixture
def fresh_login() -> dict[str, Any]:
    """A brand-new admin JWT pair so rotation tests never share refresh state."""
    resp = httpx.post(
        f"{BASE}/auth/login",
        json={"email": PERF_EMAIL, "password": PERF_PASSWORD},
        timeout=15.0,
    )
    assert resp.status_code == 200, f"login -> {resp.status_code}: {resp.text[:200]}"
    return resp.json()


@pytest.fixture
def mint(jwt_secret: str):
    """Mint a forged/access JWT for an arbitrary subject (see minting.py)."""

    def _mint(
        sub: str,
        *,
        exp_min: int = 5,
        iat_min: int = -1,
        typ: str = "access",
        secret: str | None = None,
    ):
        return mint_access(
            sub,
            secret=secret if secret is not None else jwt_secret,
            exp_min=exp_min,
            iat_min=iat_min,
            typ=typ,
        )

    return _mint


@pytest.fixture(scope="session")
def member_identity() -> dict[str, str]:
    """Discover a seeded non-superuser user (read-only DB lookup).

    The stack seeds member users (tests/infrastructure/seeder.py) but has no
    HTTP user-listing endpoint, and POST /auth/setup is single-use (409), so
    the second identity for RBAC checks is reused from the seed. Skips
    gracefully when psycopg or the test DB is unreachable.
    """
    try:
        import psycopg
    except ImportError:
        pytest.skip("psycopg not installed — cannot discover a non-superuser user for RBAC checks")
    conn_kwargs = {
        "host": os.getenv("SECURITY_DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("SECURITY_DB_PORT", os.getenv("UPCP_PORT_POSTGRES", "35434"))),
        "user": os.getenv("SECURITY_DB_USER", os.getenv("POSTGRES_USER", "upcp")),
        "password": os.getenv(
            "SECURITY_DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "upcp_local_change_me")
        ),
        "dbname": os.getenv("SECURITY_DB_NAME", os.getenv("POSTGRES_DB", "upcp")),
        "connect_timeout": 5,
    }
    try:
        with psycopg.connect(**conn_kwargs) as conn:
            row = conn.execute(
                "SELECT id, email FROM user_account "
                "WHERE is_superuser = false AND is_active = true LIMIT 1"
            ).fetchone()
    except Exception as exc:
        pytest.skip(f"cannot reach test DB to discover a non-superuser user: {exc}")
    if row is None:
        pytest.skip("no active non-superuser user seeded — RBAC 403 checks cannot run")
    return {"id": str(row[0]), "email": str(row[1])}


@pytest.fixture(scope="session")
def member_headers(member_identity: dict[str, str], jwt_secret: str) -> dict[str, str]:
    """Bearer headers for the non-superuser user (minted with the test secret)."""
    token = mint_access(member_identity["id"], secret=jwt_secret)
    return {"Authorization": f"Bearer {token}"}
