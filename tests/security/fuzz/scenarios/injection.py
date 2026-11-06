"""Fuzz scenario: injection (SPEC-0024 Phase 4).

- SQLi probes in query params and path segments: pass = 2xx/4xx with no 500
  and no SQL error text leaked in the body.
- Path traversal: pass = 400/404 (safe rejection), never 200 with file
  contents.
- XSS probes: JSON APIs may echo payloads as data; an HTML response body
  reflecting the payload is a medium finding.
"""

from __future__ import annotations

from urllib.parse import quote

from tests.security.common import check, login
from tests.security.fuzz.harness import (
    ProbeClient,
    looks_like_file_leak,
    looks_like_sql_error,
    snippet,
)

TIMEOUT = 15.0
CATEGORY = "injection"

SQLI_PAYLOADS = (
    "' OR '1'='1",
    "'; DROP TABLE users;--",
    "1' UNION SELECT null--",
    '" OR "1"="1',
)

# Encoded traversal probes (literal ../ would be normalized client-side).
TRAVERSAL_PATHS = (
    "/api/v1/projects/..%2f..%2fetc%2fpasswd",
    "/api/v1/projects/%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "/api/v1/projects/%2e%2e/%2e%2e/etc/passwd",
    "/api/v1/%2e%2e%2f%2e%2e%2fetc%2fshadow",
)

SAFE_REJECTION = {400, 404, 422}


def run(base_url: str) -> list[dict]:
    """Run injection probes against a live target; return check records."""
    base = base_url.rstrip("/")
    headers = login(base)
    checks: list[dict] = []
    client = ProbeClient(base_url=base, headers=headers, timeout=TIMEOUT, follow_redirects=False)
    try:
        # 1. SQLi in the search endpoint query parameter.
        for payload in SQLI_PAYLOADS:
            resp = client.get("/api/v1/search", params={"q": payload, "limit": 5})
            leak = looks_like_sql_error(resp.text)
            ok = 200 <= resp.status_code < 500 and leak is None
            checks.append(
                check(
                    f"sqli query /search q={payload!r}",
                    CATEGORY,
                    ok,
                    expected="2xx/4xx, no SQL error text",
                    actual=f"{resp.status_code} leak={leak!r}",
                    detail=f"GET /api/v1/search -> {resp.status_code} {snippet(resp.text)}",
                    severity="high",
                )
            )

        # 2. SQLi in projects list query params (search/status/sort_by).
        for param in ("search", "status", "sort_by"):
            payload = SQLI_PAYLOADS[len(param) % len(SQLI_PAYLOADS)]
            resp = client.get("/api/v1/projects", params={param: payload})
            leak = looks_like_sql_error(resp.text)
            ok = 200 <= resp.status_code < 500 and leak is None
            checks.append(
                check(
                    f"sqli query /projects {param}={payload!r}",
                    CATEGORY,
                    ok,
                    expected="2xx/4xx, no SQL error text",
                    actual=f"{resp.status_code} leak={leak!r}",
                    detail=f"GET /api/v1/projects?{param}=... -> {resp.status_code} {snippet(resp.text)}",
                    severity="high",
                )
            )

        # 3. SQLi in a path segment used as a lookup id (expect safe 404/4xx).
        for payload in SQLI_PAYLOADS[:3]:
            resp = client.get(f"/api/v1/projects/{quote(payload, safe='')}")
            leak = looks_like_sql_error(resp.text)
            ok = resp.status_code in SAFE_REJECTION and leak is None
            checks.append(
                check(
                    f"sqli path /projects/{{id}}={payload!r}",
                    CATEGORY,
                    ok,
                    expected="404 (safe rejection), no SQL error text",
                    actual=f"{resp.status_code} leak={leak!r}",
                    detail=f"GET path id payload -> {resp.status_code} {snippet(resp.text)}",
                    severity="high",
                )
            )

        # 4. Path traversal attempts (must not serve file contents).
        for path in TRAVERSAL_PATHS:
            resp = client.get(path)
            leak = looks_like_file_leak(resp.text)
            ok = resp.status_code in SAFE_REJECTION and leak is None
            checks.append(
                check(
                    f"path traversal {path}",
                    CATEGORY,
                    ok,
                    expected="400/404 without file contents",
                    actual=f"{resp.status_code} leak={leak!r}",
                    detail=f"GET {path} -> {resp.status_code} {snippet(resp.text)}",
                    severity="critical",
                )
            )

        # 5. XSS: reflection in a JSON search response is data, not a finding;
        #    an HTML content-type echoing the payload would be medium.
        script = "<script>alert('upcp-fuzz')</script>"
        resp = client.get("/api/v1/search", params={"q": script, "limit": 5})
        ctype = resp.headers.get("content-type", "")
        ok = resp.status_code < 500 and "text/html" not in ctype.lower()
        checks.append(
            check(
                "xss reflected in /search result",
                CATEGORY,
                ok,
                expected="non-HTML response, no 500",
                actual=f"{resp.status_code} content-type={ctype}",
                detail=f"q={script!r} -> {resp.status_code} {snippet(resp.text)}",
                severity="medium",
            )
        )

        # 6. XSS stored/echoed via a create field (JSON echo = OK, HTML = not).
        #    Creates at most 1 row for this scenario; slug stays unique.
        import uuid

        name = f"{script} xss-{uuid.uuid4().hex[:8]}"
        resp = client.post("/api/v1/projects", json={"name": name, "description": "fuzz xss probe"})
        ctype = resp.headers.get("content-type", "")
        reflected = script in resp.text
        ok = resp.status_code < 500 and "text/html" not in ctype.lower()
        checks.append(
            check(
                "xss echoed by project create",
                CATEGORY,
                ok,
                expected="2xx/4xx JSON response without HTML execution context",
                actual=f"{resp.status_code} content-type={ctype} reflected={reflected}",
                detail=f"POST /api/v1/projects with script payload -> {resp.status_code} {snippet(resp.text)}",
                severity="medium",
            )
        )
    finally:
        client.close()
    return checks
