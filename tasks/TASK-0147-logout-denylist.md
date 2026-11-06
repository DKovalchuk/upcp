# TASK-0147 — SPEC-0027 S27.3: Logout access-token denylist

**Spec:** `specs/SPEC-0027-security-findings-closure.md` §3.3 (finding 3)
**Milestone:** SPEC-0027 (Этап 1)
**Points:** 5
**Status:** DONE (closed 2026-10-24)
**Depends on:** TASK-0146 (same middleware file — merge order)

## Objective

Access token rejected immediately after logout: Redis denylist keyed by
token fingerprint, enforced in AuthMiddleware AND `get_current_user`.

## Acceptance Criteria (verified 2026-10-24)

- [x] `AuthService.logout()` adds `auth:deny:{sha256(raw_token)}` = 1,
      TTL = `exp - now` (self-expiring, no cleanup job; `_access_ttl`
      clamps to ≥1s, bounded fallback `ACCESS_TOKEN_EXPIRY`)
- [x] Shared helper `is_token_denied(token)` checked in AuthMiddleware
      (user-JWT path, post-signature) and `get_current_user` (post-verify) —
      401 same shape as invalid token
- [x] Redis down → fail-open (allow) + structured warning log
      (`action=auth.denylist_unavailable`, documented tradeoff)
- [x] Denylist distinguishable from expiry in logs (audit field:
      rejection logs `action=auth.token_denied`, `reason=logout` + metric
      `upcp_auth_token_denials_total{reason}` + OTel span attrs)
- [x] **Red first:** hermetic `test_logout_denylist.py` red — **4 failed /
      1 passed** (refresh-preservation pin) → green **5/5** (domain route
      AND `/auth/me` 401 after login → logout; key fingerprint + TTL
      asserts; redis-down fail-open + warning)
- [x] Live authz suite: `test_access_token_rejected_after_logout` —
      xfail removed, strict pass; **0 xfail** in whole authz suite (AC8):
      **55 passed, 1 skipped**
- [x] Full backend suite green (**989 passed**, 3 pre-existing `test_redis`
      env-failures); ruff + format clean; `mypy backend/app` no issues (114)

## Evidence

- Hermetic red→green: **5/5** (red: 4 failed / 1 passed-preservation)
- Full backend: **989 passed / 3 failed** — all 3 = pre-existing local
  `redis` package gap (baseline-confirmed in TASK-0145)
- Live stack (compose up → seeder → suite → stop): **55 passed / 1 skipped
  / 0 xfailed** — finding-3 strict; SPEC-0027 authz suite now runs
  **0 xfail** (findings 1-3 closed)
- Env gotchas hit & fixed:
  1. `denylist.py` was created with 600 perms → container bind-mount
     (`./backend/app:/app/app`) crash-looped on
     `PermissionError: denylist.py` — chmod 644 (mount is read by the
     container uid, not the file owner)
  2. `/auth/login` limit (5/min) vs 6 suite logins (1 session admin +
     5× `fresh_login`) → deterministic 429 on the 6th login, previously
     **masked by the non-strict finding-3 xfail** (setup errors counted
     as xfail) — `fresh_login` now waits out `retry_after` once and
     retries (+61s per suite run); production limit untouched

## Deviations (recorded per §7)

1. **Denylist WRITE also fail-open.** Spec defines fail-open for the READ
   path (AC5); a Redis outage during logout degrades the same way —
   refresh revocation + audit still commit, the access token stays valid
   only until exp (≤15 min) with `action=auth.denylist_write_failed`
   warning.
2. **Order-independence in tests:** `login()` commits (audit invariant),
   so committed test users survived `db_session` rollback and poisoned
   later files assuming an empty user table (`POST /auth/setup` first-run
   check — surfaced when the new file ran before `test_auth_endpoints`).
   `test_logout_denylist.py` purges its rows in teardown (`_purge_user`).

## Files

| File | Action |
|------|--------|
| `backend/app/identity/denylist.py` | CREATE — fingerprint, deny/read/write, rejection telemetry |
| `backend/app/identity/service.py` | MODIFY — logout denylist write + `_access_ttl` |
| `backend/app/identity/endpoints.py` | MODIFY — logout passes the raw access token |
| `backend/app/identity/auth.py` | MODIFY — `get_current_user` deny check |
| `backend/app/identity/middleware.py` | MODIFY — user-JWT deny check |
| `backend/app/shared/metrics.py` | MODIFY — `upcp_auth_token_denials_total` |
| `backend/tests/test_logout_denylist.py` | CREATE (red→green, 5 tests) |
| `backend/tests/test_auth_commit_before_respond.py` | MODIFY — logout signature |
| `tests/security/authz/test_tokens.py` | MODIFY — remove xfail (finding 3) |
| `tests/security/authz/conftest.py` | MODIFY — `fresh_login` 429 retry |
