# TASK-0147 — SPEC-0027 S27.3: Logout access-token denylist

**Spec:** `specs/SPEC-0027-security-findings-closure.md` §3.3 (finding 3)
**Milestone:** SPEC-0027 (Этап 1)
**Points:** 5
**Status:** PENDING
**Depends on:** TASK-0146 (same middleware file — merge order)

## Objective

Access token rejected immediately after logout: Redis denylist keyed by
token fingerprint, enforced in AuthMiddleware AND `get_current_user`.

## Acceptance Criteria

- [ ] `AuthService.logout()` adds `auth:deny:{sha256(raw_token)}` = 1,
      TTL = `exp - now` (self-expiring, no cleanup job)
- [ ] Shared helper `is_token_denied(token)` checked in AuthMiddleware
      (user-JWT path, post-signature) and `get_current_user` (post-verify) —
      401 same shape as invalid token
- [ ] Redis down → fail-open (allow) + structured warning log (documented tradeoff)
- [ ] Denylist distinguishable from expiry in logs (audit field)
- [ ] **Red first:** unit test login → logout → same access token → 401 on
      domain route AND `/auth/me` (currently works — red → green)
- [ ] Live authz suite: `test_access_token_rejected_after_logout` —
      xfail removed, strict pass; **0 xfail** in whole authz suite (AC8)
- [ ] Full backend suite green; ruff + mypy clean

## Files

| File | Action |
|------|--------|
| `backend/app/identity/service.py` | MODIFY — denylist write on logout |
| `backend/app/identity/auth.py` | MODIFY — `get_current_user` denylist check |
| `backend/app/identity/middleware.py` | MODIFY — denylist check |
| `backend/tests/test_logout_denylist.py` | CREATE (red→green) |
| `tests/security/authz/test_tokens.py` | MODIFY — remove xfail (finding 3) |
