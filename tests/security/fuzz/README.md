# UPCP API Fuzzer Suite

Static/active API fuzzing for the live test stack — SPEC-0024 Phase 4 (TASK-0142).
Part of `tests/security/` (profiles in `config/security_profiles.yaml`).

## Usage

```bash
# from the repo root (module invocation is the contract for the top-level runner)
python -m tests.security.fuzz --out /tmp/fuzz.json

# env fallback for the output path
SECURITY_RESULT_OUT=/tmp/fuzz.json python -m tests.security.fuzz

# extras
python -m tests.security.fuzz --list
python -m tests.security.fuzz --scenario injection --out /tmp/inj.json

# hermetic unit tests (no network; clear addopts=cov and pythonpath=backend —
# backend/tests would otherwise shadow the repo-root `tests` package)
python -m pytest tests/security/fuzz/test_fuzz_unit.py -o addopts= -o pythonpath=
```

Environment: `SECURITY_BASE_URL` (default `http://localhost:38082`),
`PERF_EMAIL` / `PERF_PASSWORD` (default seeded admin). Requires the test stack
to be up (`GET /health` → 200). Rate limiting is disabled on this stack, so the
suite never expects 429.

**Exit codes:** `0` all checks passed · `1` some checks failed (see `findings`)
· `2` could not run (target down / login failed).

## Scenarios

| Scenario      | What it fuzzes                                                                 |
| ------------- | ------------------------------------------------------------------------------ |
| `auth_bypass` | No-token access to `/api/v1/*`, `/mcp`, admin-ish reads; HTTP method tricks; malformed/tampered/wrong-scheme JWTs; agent endpoints without `X-Agent-Token` |
| `injection`   | SQLi payloads in query params and path segments, path traversal (`%2e%2e%2f`), XSS reflection in search/create (HTML echo = medium finding) |
| `malformed`   | 1MB payloads, wrong types, missing fields, nulls, null bytes, unicode-only names, 200-level nesting, `limit=100000`, invalid enums |

Each scenario is a module under `scenarios/` exposing
`run(base_url: str) -> list[check-dict]`; discovery goes through the
`SCENARIOS` registry in `runner.py` (mirrors `tests/chaos/runner.py`).

**Pass semantics:** a check fails only when the app actually misbehaves —
HTTP 500, auth bypass success, SQL/file content or traceback leaked in the
body. Validation rejections (400/404/405/422) are passes. Read-only toward
existing data: no deletes, at most one row created per scenario run.

## Output schema

One JSON document written to `--out`, built via
`tests.security.common.summarize(suite="fuzz", ...)`:

```json
{
  "schema": "upcp-security-result/v1",
  "suite": "fuzz",
  "target": "http://localhost:38082",
  "checks": [{"name": "...", "category": "auth_bypass", "status": "pass|fail",
              "expected": "...", "actual": "...", "detail": "...", "severity": "..."}],
  "findings": [{"severity": "high", "title": "...", "category": "...", "detail": "..."}],
  "summary": {"total": 0, "passed": 0, "failed": 0},
  "scenario_counts": {"auth_bypass": {"total": 0, "passed": 0, "failed": 0, "duration_seconds": 0.0}},
  "duration_seconds": 0.0
}
```
