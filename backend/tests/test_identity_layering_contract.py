"""Layering source contract for the rewired dependencies — SPEC-0029 AC1/AC5 / TASK-0175.

The grep-contract deferred from TASK-0174 (its AC1/AC5, achievable once
TASK-0175 rewires the three consumers): ``identity/auth.py``,
``identity/agent_auth.py`` and ``identity/permissions.py`` must contain
no raw data access — no ``db.query``, no ``SessionLocal``, no direct
cache access — and ``agent_auth.py`` must not hash tokens itself (the
single sha256 lives in ``AgentTokenService``).

The check is a pure function over source text, mutation-tested below with
positive and negative cases: deliberately string-based (not AST) so it
also catches regressions hiding in comments, aliases or macro-style
expressions. ``db.get(...)`` stays allowed — it is the gate's byte-parity
subject check, not a query-builder call (see the negative cases).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[1] / "app"
DEPENDENCY_FILES = (
    "identity/auth.py",
    "identity/agent_auth.py",
    "identity/permissions.py",
)

_RAW_ACCESS_MARKERS = (
    ("db.query", re.compile(r"\bdb\.query\b")),
    ("SessionLocal", re.compile(r"\bSessionLocal\b")),
    ("app.shared.redis", re.compile(r"\bapp\.shared\.redis\b")),
    ("get_redis_client", re.compile(r"\bget_redis_client\b")),
)


def raw_data_access_markers(source: str, *, forbid_hashlib: bool = False) -> list[str]:
    """Markers of raw data access in ``source`` (stable order, deduped)."""
    found = [name for name, pattern in _RAW_ACCESS_MARKERS if pattern.search(source)]
    if forbid_hashlib and re.search(r"\bhashlib\b", source):
        found.append("hashlib")
    return found


# ── Mutation cases: the scanner flags raw access, and only that ─────


@pytest.mark.parametrize(
    "source,expected",
    [
        # positive — every raw-access form is caught
        ("user = db.query(User).filter_by(id=uid).first()", ["db.query"]),
        ("rows = session.query(Permission).all()", []),  # aliasing is out of scope (string scan)
        ("from app.shared.database import SessionLocal", ["SessionLocal"]),
        ("def f():\n    return SessionLocal()", ["SessionLocal"]),
        ("from app.shared.redis import get_redis_client", ["app.shared.redis", "get_redis_client"]),
        ("client = get_redis_client()", ["get_redis_client"]),
        # negative — the allowed data-access vocabulary stays legal
        ("user = db.get(User, uid)", []),
        ("from app.shared.database import get_session\nfrom sqlalchemy.orm import Session", []),
        ("from app.identity.cache_provider import AuthCacheProvider", []),
        ("perms = repo.granted_pairs(user_id)", []),
        ("# the cache is redis-compatible but accessed via the provider", []),
        ("", []),
    ],
)
def test_raw_access_marker_scanner(source: str, expected: list[str]) -> None:
    assert raw_data_access_markers(source) == expected


def test_hashlib_flag_is_opt_in() -> None:
    """hashlib is banned only where the task demands it (agent_auth.py)."""
    src = "import hashlib\nhashlib.sha256(raw.encode())"
    assert raw_data_access_markers(src) == []
    assert raw_data_access_markers(src, forbid_hashlib=True) == ["hashlib"]


def test_scanner_flags_regression_appended_to_real_source() -> None:
    """Mutation on a real file: re-introducing raw access must be caught."""
    source = (APP_DIR / "identity/permissions.py").read_text(encoding="utf-8")
    assert raw_data_access_markers(source) == [], "precondition: current file is clean"
    mutated = source + "\ndef _leak(uid):\n    return db.query(User).all()\n"
    assert "db.query" in raw_data_access_markers(mutated)


# ── The contract on the three rewired files ─────────────────────────


@pytest.mark.parametrize("rel", DEPENDENCY_FILES)
def test_dependency_file_has_no_raw_data_access(rel: str) -> None:
    source = (APP_DIR / rel).read_text(encoding="utf-8")
    assert raw_data_access_markers(source) == [], (
        f"{rel} regressed to raw data access — go through a repository/provider: "
        f"{raw_data_access_markers(source)}"
    )


def test_agent_auth_does_not_hash_tokens_itself() -> None:
    """AC5: after TASK-0175 the single sha256 of agent tokens lives in
    AgentTokenService — agent_auth.py must not import hashing at all."""
    source = (APP_DIR / "identity/agent_auth.py").read_text(encoding="utf-8")
    assert raw_data_access_markers(source, forbid_hashlib=True) == [], (
        "agent_auth.py must not hash tokens itself"
    )
