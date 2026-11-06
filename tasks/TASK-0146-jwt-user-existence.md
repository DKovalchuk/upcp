# TASK-0146 — SPEC-0027 S27.2: Middleware user-existence check + Redis cache

**Spec:** `specs/SPEC-0027-security-findings-closure.md` §3.2 (finding 2)
**Milestone:** SPEC-0027 (Этап 1)
**Points:** 5
**Status:** DONE (closed 2026-10-24)

## Objective

AuthMiddleware (user-JWT path): reject tokens whose `sub` does not exist
or whose user is disabled — even when signature is valid. Negative caching.

## Acceptance Criteria (verified 2026-10-24)

- [x] After `verify_access_token`: cache `auth:user:{sub}` state
      ("active"/"unknown"/"disabled" per SPEC §3.2 — richer than the
      "1"/"0" sketch; the state feeds the rejection-reason log/metric),
      TTL 60s, negative caching included
- [x] Miss → DB check `user_account` exists AND active; absent/disabled → 401
      with `WWW-Authenticate` (same shape as invalid token)
- [x] Agent-token path unchanged (already DB-checked)
- [x] Redis down → direct DB query per request (no auth bypass possible)
- [x] **Red first:** hermetic `test_auth_middleware_user_check.py` written
      red → green **5/5** (valid-signature JWT with nonexistent sub → 401)
- [x] Cache-hit test: second request → no DB hit (spy counter on
      `_fetch_user_state`; negative cache asserted for a fresh unknown sub)
- [x] Live authz suite: `test_nonexistent_user_rejected_on_domain_endpoint` —
      xfail removed, strict pass; run: **54 passed, 1 skipped, 1 xfailed**
      (remaining xfail = finding 3 → TASK-0147)
- [x] Full backend suite green (**984 passed**, 3 pre-existing `test_redis`
      env-failures); ruff + format clean; `mypy backend/app` no issues (113)

## Evidence

- Hermetic subject-check **5/5**: unknown→401, disabled→401, active→200,
  negative-cache DB-hit counter, redis-outage→DB fallback
- Full backend: **984 passed / 3 failed** (all 3 = pre-existing local
  `redis` package gap, baseline-confirmed in TASK-0145)
- Live stack (compose up → seeder → suite → stop): **54 passed / 1 skipped
  / 1 xfailed** — finding-2 strict; finding-3 xfail remains
- Env gotchas hit: seeder needs `alembic` via `.venv/bin` on PATH; shell
  `UPCP_SECRET_KEY=change_me_local_only` vs conftest fallback
  `test_secret_for_quality_gate_only` — mint/verify aligned by passing the
  same explicit secret to compose and the live run

## Collateral (hermetic contract)

Middleware now resolves `SessionLocal` lazily per request — hermetic tests
got an autouse conftest redirect to `_TestSession` (the compose-only host
`db` is unreachable from the runner; live suites under `tests/security/`
keep their own conftest/real factory) plus a `seed_subject` fixture for
tests minting fixed subs (`user-123`/`user-456`) in 4 files.

## Files

| File | Action |
|------|--------|
| `backend/app/identity/middleware.py` | MODIFY — subject check + cache + rejection |
| `backend/app/shared/metrics.py` | MODIFY — `upcp_auth_subject_rejections_total` |
| `backend/tests/test_auth_middleware_user_check.py` | CREATE (red→green, 5 tests) |
| `backend/tests/conftest.py` | MODIFY — SessionLocal redirect + `seed_subject` |
| `backend/tests/test_auth_middleware_protection.py` etc. (4 files) | MODIFY — subject seeding |
| `backend/tests/test_rbac_enforcement.py` | MODIFY — docstring (finding 2 closed) |
| `tests/security/authz/test_tokens.py` | MODIFY — remove xfail (finding 2) |
