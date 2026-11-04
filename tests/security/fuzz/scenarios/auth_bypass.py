"""Fuzz scenario: auth_bypass (SPEC-0024 Phase 4).

Probes anonymous and tampered-credential access to protected surfaces:
- no token on existing protected paths (expect 401)
- HTTP method tricks without auth (never 2xx/5xx — 401 on a routed
  method, 405 when the method is not routed at all; SPEC-0028 D2 moved
  auth into route dependencies, so dispatch decisions happen first)
- malformed / tampered / wrong-scheme Authorization headers
- agent self-service endpoints without a valid X-Agent-Token
"""

from __future__ import annotations

import httpx

from tests.security.common import check, login
from tests.security.fuzz.harness import (
    ProbeClient,
    garbage_jwt,
    snippet,
    tamper_payload,
    tamper_signature,
)

TIMEOUT = 15.0
CATEGORY = "auth_bypass"

# Protected read surfaces — REAL existing paths only: since SPEC-0028 D2
# auth lives in route dependencies, so a phantom path answers 404 before
# auth runs (the retired AuthMiddleware answered 401 pre-routing and
# masked dead probes). /mcp carries a trailing slash to skip the 307.
NO_AUTH_GET = (
    "/api/v1/projects",
    "/api/v1/agents",
    "/api/v1/audit/export",
    "/api/v1/tasks/00000000-0000-0000-0000-000000000000",
    "/api/v1/dashboard/stats",
    "/api/v1/agent/me",
    "/mcp/",
)

# Method tricks: an unauthenticated write must never succeed. Since D2 the
# refusal is 401 (route exists, auth denies) or 405 (method not routed —
# no handler runs either; the route inventory is public via /openapi.json
# anyway). Never 2xx/5xx is the invariant that matters.
METHOD_TRICKS = (
    ("POST", "/api/v1/projects"),
    ("PUT", "/api/v1/projects"),
    ("PATCH", "/api/v1/projects"),
    ("DELETE", "/api/v1/projects"),
    ("PATCH", "/api/v1/projects/11111111-1111-1111-1111-111111111111"),
    ("DELETE", "/api/v1/projects/11111111-1111-1111-1111-111111111111"),
    ("POST", "/api/v1/search"),
)

# Denials accepted for method tricks under D2 (see METHOD_TRICKS).
_METHOD_TRICK_DENIALS = (401, 405)


def _expect_401(
    checks: list[dict], name: str, resp: httpx.Response, severity: str = "high"
) -> None:
    checks.append(
        check(
            name,
            CATEGORY,
            resp.status_code == 401,
            expected="401",
            actual=str(resp.status_code),
            detail=f"-> {resp.status_code} {snippet(resp.text)}",
            severity=severity,
        )
    )


def _expect_denied(
    checks: list[dict], name: str, resp: httpx.Response, allowed: tuple[int, ...]
) -> None:
    """Refused, never successful: status in ``allowed`` and below 500."""
    checks.append(
        check(
            name,
            CATEGORY,
            resp.status_code in allowed and resp.status_code < 500,
            expected=f"{'/'.join(str(s) for s in allowed)} (never 2xx/5xx)",
            actual=str(resp.status_code),
            detail=f"-> {resp.status_code} {snippet(resp.text)}",
            severity="high",
        )
    )


def run(base_url: str) -> list[dict]:
    """Run auth bypass probes against a live target; return check records."""
    base = base_url.rstrip("/")
    token = login(base)["Authorization"].removeprefix("Bearer ")
    checks: list[dict] = []
    anon = ProbeClient(base_url=base, timeout=TIMEOUT, follow_redirects=False)
    try:
        # 1. Anonymous access to protected read endpoints.
        for path in NO_AUTH_GET:
            _expect_401(checks, f"no-token GET {path}", anon.get(path))

        # 2. Anonymous write attempts via assorted HTTP methods.
        for method, path in METHOD_TRICKS:
            resp = anon.request(method, path)
            _expect_denied(checks, f"no-token {method} {path}", resp, _METHOD_TRICK_DENIALS)

        # 3. Anonymous MCP JSON-RPC POST (slash form — no 307 redirect).
        _expect_401(checks, "no-token POST /mcp/", anon.post("/mcp/", json={}))

        # 4. Malformed / tampered credentials on a protected endpoint.
        bad_credentials = (
            ("malformed bearer (garbage)", {"Authorization": "Bearer garbage"}),
            ("empty bearer value", {"Authorization": "Bearer"}),
            ("wrong auth scheme (Token)", {"Authorization": f"Token {token}"}),
            ("tampered JWT signature", {"Authorization": f"Bearer {tamper_signature(token)}"}),
            ("tampered JWT payload", {"Authorization": f"Bearer {tamper_payload(token)}"}),
            ("unsigned alg:none-style JWT", {"Authorization": f"Bearer {garbage_jwt()}"}),
        )
        for label, headers in bad_credentials:
            resp = anon.get("/api/v1/projects", headers=headers)
            _expect_401(checks, f"bad credential: {label}", resp, severity="critical")

        # 5. Agent self-service endpoint requires X-Agent-Token, not just JWT.
        valid_jwt = {"Authorization": f"Bearer {token}"}
        _expect_401(
            checks,
            "agent/me with JWT but no X-Agent-Token",
            anon.get("/api/v1/agent/me", headers=valid_jwt),
        )
        _expect_401(
            checks,
            "agent/me with JWT + garbage X-Agent-Token",
            anon.get("/api/v1/agent/me", headers={**valid_jwt, "X-Agent-Token": "garbage"}),
        )
        _expect_401(
            checks,
            "agent/me with garbage X-Agent-Token only",
            anon.get("/api/v1/agent/me", headers={"X-Agent-Token": "garbage"}),
        )
    finally:
        anon.close()
    return checks
