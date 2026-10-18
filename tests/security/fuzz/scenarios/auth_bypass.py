"""Fuzz scenario: auth_bypass (SPEC-0024 Phase 4).

Probes anonymous and tampered-credential access to protected surfaces:
- no token on /api/v1/* and /mcp (expect 401)
- HTTP method tricks without auth (expect 401, not 405/500)
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

# Protected read surfaces (domain API, agent registry, admin-ish, MCP).
NO_AUTH_GET = (
    "/api/v1/projects",
    "/api/v1/agents",
    "/api/v1/audit/logs",
    "/api/v1/tasks",
    "/api/v1/dashboard",
    "/api/v1/agent/me",
    "/mcp",
)

# Method tricks: unauthenticated writes must be rejected with 401 before any
# method-based dispatch (never 405/500, never success).
METHOD_TRICKS = (
    ("POST", "/api/v1/projects"),
    ("PUT", "/api/v1/projects"),
    ("PATCH", "/api/v1/projects"),
    ("DELETE", "/api/v1/projects"),
    ("PATCH", "/api/v1/projects/11111111-1111-1111-1111-111111111111"),
    ("DELETE", "/api/v1/projects/11111111-1111-1111-1111-111111111111"),
    ("POST", "/api/v1/search"),
)


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
            _expect_401(checks, f"no-token {method} {path}", resp)

        # 3. Anonymous MCP JSON-RPC POST.
        _expect_401(checks, "no-token POST /mcp", anon.post("/mcp", json={}))

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
