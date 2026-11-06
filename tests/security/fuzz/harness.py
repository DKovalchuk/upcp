"""Shared helpers for fuzz scenarios (TASK-0142 / SPEC-0024 Phase 4).

Pure helpers here are unit-tested in tests/security/fuzz/test_fuzz_unit.py
without any network access.
"""

from __future__ import annotations

import base64
import json

import httpx

# Markers that indicate a backend SQL/database error leaked into the response.
SQL_ERROR_MARKERS: tuple[str, ...] = (
    "sqlalchemy",
    "psycopg",
    "sql syntax",
    "syntax error at",
    "sqlite_",
    "ora-009",
    "programmingerror",
    "statementerror",
    "dbapierror",
    "relation does not exist",
    "column ",
    "you have an error in your sql syntax",
    "traceback (most recent call last)",
)

# Markers that indicate Unix file contents leaked through a traversal probe.
FILE_LEAK_MARKERS: tuple[str, ...] = (
    "root:x:0:0",
    "/bin/bash",
    "/bin/sh",
    "daemon:",
    "nobody:x:",
)

MAX_BODY_SNIPPET = 240


def _first_marker(text: str, markers: tuple[str, ...]) -> str | None:
    """Return the first marker found in text (case-insensitive), else None."""
    low = text.lower()
    for marker in markers:
        if marker in low:
            return marker
    return None


def looks_like_sql_error(body: str) -> str | None:
    """Return the matched leak marker when the body exposes a SQL/DB error."""
    return _first_marker(body, SQL_ERROR_MARKERS)


def looks_like_file_leak(body: str) -> str | None:
    """Return the matched leak marker when the body looks like file contents."""
    return _first_marker(body, FILE_LEAK_MARKERS)


def snippet(text: str, limit: int = MAX_BODY_SNIPPET) -> str:
    """Truncate a response body down to a short single-line evidence snippet."""
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."


def _b64url_json(obj: object) -> str:
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64url_decode(segment: str) -> bytes:
    padded = segment + "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(padded)


def tamper_signature(token: str) -> str:
    """Return the JWT with its signature altered (verification must fail)."""
    parts = token.split(".")
    if len(parts) == 3 and parts[2]:
        head = "A" if parts[2][0] != "A" else "B"
        parts[2] = head + parts[2][1:]
    return ".".join(parts)


def tamper_payload(token: str) -> str:
    """Return the JWT with modified claims while keeping the old signature.

    A correct implementation must reject this because the signature no longer
    matches the payload.
    """
    parts = token.split(".")
    if len(parts) == 3:
        try:
            claims = json.loads(_b64url_decode(parts[1]))
        except (ValueError, TypeError):
            claims = {"sub": "fuzzed"}
        if not isinstance(claims, dict):
            claims = {"sub": "fuzzed"}
        claims["fuzzed_by"] = "upcp-fuzz"
        parts[1] = _b64url_json(claims)
    return ".".join(parts)


def garbage_jwt() -> str:
    """Well-shaped but unsigned 'alg: none'-style token (must be rejected)."""
    header = _b64url_json({"alg": "none", "typ": "JWT"})
    payload = _b64url_json({"sub": "admin", "role": "admin"})
    return f"{header}.{payload}.fuzzed"


class ProbeClient(httpx.Client):
    """httpx.Client hardened against stale pooled connections.

    The test-stack app closes keep-alive connections after 500 responses
    without sending ``Connection: close``, so an immediate follow-up request
    reusing the pooled connection is dropped before a response arrives. A
    probe must never crash the scenario because of that, so one retry on a
    fresh connection is made; if it still fails, a synthetic 599 response is
    returned — 599 satisfies no scenario's pass condition, so the probe is
    recorded as a failed check with the transport error as evidence.
    """

    def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        try:
            return super().request(method, url, **kwargs)  # type: ignore[arg-type]
        except httpx.TransportError:
            pass
        try:
            return super().request(method, url, **kwargs)  # type: ignore[arg-type]
        except httpx.TransportError as exc:
            detail = f"transport error after retry: {type(exc).__name__}: {exc}"
            return httpx.Response(599, content=detail.encode())
