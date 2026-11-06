"""Fuzz scenario: malformed (SPEC-0024 Phase 4).

- Oversized payloads: 4xx/413, never 500.
- Wrong types / missing fields / nulls: 422, never 500.
- Null-byte, unicode and deeply nested values: must not trigger 500.
- Huge pagination values: capped or 4xx, never 500/OOM.

Read-only toward existing data: creates at most 1 row across the scenario
(deep-nesting probe, fixed name so re-runs hit a 409 conflict instead).
"""

from __future__ import annotations

import httpx

from tests.security.common import check, login
from tests.security.fuzz.harness import ProbeClient, snippet

TIMEOUT = 60.0
CATEGORY = "malformed"

PROJECTS = "/api/v1/projects"
VALIDATION_ERRORS = {400, 422}
OVERSIZE_ERRORS = {400, 413, 422}


def run(base_url: str) -> list[dict]:
    """Run malformed-input probes against a live target; return check records."""
    base = base_url.rstrip("/")
    headers = login(base)
    checks: list[dict] = []
    client = ProbeClient(base_url=base, headers=headers, timeout=TIMEOUT, follow_redirects=False)
    try:
        _payload_checks(client, checks)
        _nesting_and_text_checks(client, checks)
        _query_param_checks(client, checks)
    finally:
        client.close()
    return checks


def _payload_checks(client: httpx.Client, checks: list[dict]) -> None:
    """Body-level validation probes: wrong types, missing fields, oversized."""
    oversized = "A" * (1024 * 1024)
    cases: list[tuple[str, object, set[int]]] = [
        ("oversized 1MB name", {"name": oversized, "description": "x"}, OVERSIZE_ERRORS),
        ("missing required fields", {}, VALIDATION_ERRORS),
        ("wrong type: name as int", {"name": 123}, VALIDATION_ERRORS),
        ("array where scalar expected", {"name": ["a", "b"]}, VALIDATION_ERRORS),
        ("null where string expected", {"name": None}, VALIDATION_ERRORS),
    ]
    for label, payload, allowed in cases:
        resp = client.post(PROJECTS, json=payload)
        _record(
            checks,
            label,
            resp,
            expected=f"{'/'.join(str(s) for s in sorted(allowed))} validation error",
            allowed=allowed,
        )

    resp = client.post(PROJECTS, content=b"{bad json", headers={"Content-Type": "application/json"})
    _record(
        checks,
        "malformed raw JSON body",
        resp,
        expected="400/422 validation error",
        allowed=VALIDATION_ERRORS,
    )


def _nesting_and_text_checks(client: httpx.Client, checks: list[dict]) -> None:
    """Content-level probes: null bytes, unicode-only names, deep nesting."""
    nested: dict[str, object] = {"name": "deep-nest-fuzz"}
    cursor = nested
    for _ in range(200):
        cursor["child"] = {}
        cursor = cursor["child"]

    null_byte_name = "fuzz" + chr(0) + "null"
    cases: list[tuple[str, object]] = [
        ("null byte inside name string", {"name": null_byte_name, "description": "x"}),
        ("unicode-only name (Cyrillic)", {"name": "проект фазз", "description": "x"}),
        ("deeply nested body (200 levels)", nested),
    ]
    for label, payload in cases:
        resp = client.post(PROJECTS, json=payload)
        # Accept any 2xx/4xx — the only failure mode is an unhandled 500.
        _record(
            checks,
            label,
            resp,
            expected="status < 500",
            allowed=set(range(200, 500)),
        )


def _query_param_checks(client: httpx.Client, checks: list[dict]) -> None:
    """Query-level validation probes: bad types, negatives, huge batches."""
    cases: list[tuple[str, str, str]] = [
        ("query limit as string", "limit", "abc"),
        ("negative query limit", "limit", "-1"),
        ("huge batch limit=100000", "limit", "100000"),
        ("query offset as string", "offset", "abc"),
        ("huge offset value", "offset", "999999999999999"),
    ]
    for label, param, value in cases:
        resp = client.get(PROJECTS, params={param: value})
        capped = resp.status_code == 200 and _item_count(resp) <= 100
        ok = resp.status_code in VALIDATION_ERRORS or capped
        checks.append(
            check(
                label,
                CATEGORY,
                ok,
                expected="422 (or capped 2xx response)",
                actual=str(resp.status_code),
                detail=f"GET {PROJECTS}?{param}={value} -> {resp.status_code} {snippet(resp.text)}",
                severity="medium",
            )
        )

    resp = client.patch(
        f"{PROJECTS}/11111111-1111-1111-1111-111111111111",
        json={"status": "not-a-status"},
    )
    _record(
        checks,
        "patch with invalid status enum",
        resp,
        expected="422 validation error (or 404)",
        allowed=VALIDATION_ERRORS | {404},
    )


def _item_count(resp: httpx.Response) -> int:
    try:
        data = resp.json()
    except ValueError:
        return 0
    items = data.get("items") if isinstance(data, dict) else None
    return len(items) if isinstance(items, list) else 0


def _record(
    checks: list[dict],
    label: str,
    resp: httpx.Response,
    *,
    expected: str,
    allowed: set[int],
    severity: str = "medium",
) -> None:
    checks.append(
        check(
            f"malformed: {label}",
            CATEGORY,
            resp.status_code in allowed,
            expected=expected,
            actual=str(resp.status_code),
            detail=f"-> {resp.status_code} {snippet(resp.text)}",
            severity=severity,
        )
    )
