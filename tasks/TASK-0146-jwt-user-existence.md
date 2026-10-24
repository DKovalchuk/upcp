# TASK-0146 — SPEC-0027 S27.2: Middleware user-existence check + Redis cache

**Spec:** `specs/SPEC-0027-security-findings-closure.md` §3.2 (finding 2)
**Milestone:** SPEC-0027 (Этап 1)
**Points:** 5
**Status:** PENDING

## Objective

AuthMiddleware (user-JWT path): reject tokens whose `sub` does not exist
or whose user is disabled — even when signature is valid. Negative caching.

## Acceptance Criteria

- [ ] After `verify_access_token`: cache `auth:user:{sub}` = "1"/"0", TTL 60s
      (negative caching included)
- [ ] Miss → DB check `user_account` exists AND active; absent/disabled → 401
      with `WWW-Authenticate` (same shape as invalid token)
- [ ] Agent-token path unchanged (already DB-checked)
- [ ] Redis down → direct DB query per request (no auth bypass possible)
- [ ] **Red first:** unit test valid-signature JWT with nonexistent sub →
      domain GET → 401 (currently 200 — write, run, fail, implement, pass)
- [ ] Cache-hit test: second request → no DB hit (spy/counter)
- [ ] Live authz suite: `test_nonexistent_user_rejected_on_domain_endpoint` —
      xfail removed, strict pass
- [ ] Full backend suite green; ruff + mypy clean

## Files

| File | Action |
|------|--------|
| `backend/app/identity/middleware.py` | MODIFY — existence check |
| `backend/tests/test_auth_middleware_user_check.py` | CREATE (red→green) |
| `tests/security/authz/test_tokens.py` | MODIFY — remove xfail (finding 2) |
