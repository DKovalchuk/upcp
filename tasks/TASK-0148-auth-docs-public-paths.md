# TASK-0148 — SPEC-0027 S27.4: Password-change revocation + docs rewrite + PUBLIC_PATHS

**Spec:** `specs/SPEC-0027-security-findings-closure.md` §3.4 (findings 4-5)
**Milestone:** SPEC-0027 (Этап 1)
**Points:** 3
**Status:** PENDING
**Depends on:** TASK-0145 (docs must document its gates)

## Objective

Close doc-code mismatch honestly: implement promised refresh-revocation on
password change, rewrite `docs/security/auth-rbac.md` to actual behavior,
remove dead `/mcp/health` from PUBLIC_PATHS.

## Acceptance Criteria

- [ ] **Red first:** `change_password` success → ALL user's refresh tokens
      revoked (test: old refresh rotate → 401); currently fails → implement → pass
- [ ] Access JWTs of other sessions stay valid until exp — documented as limitation
- [ ] `docs/security/auth-rbac.md` rewritten: paths `/auth/*` (не
      `/api/v1/auth/*`), actual claims `sub/type/iat/exp` (нет jti,
      roles/scopes), denylist + Redis-degradation note, password-change
      semantics, `require_permission` usage example (после TASK-0145)
- [ ] Doc-literal test: logout path in docs == code route
- [ ] `/mcp/health` removed from `PUBLIC_PATHS`; regression test: every
      PUBLIC_PATHS entry resolves to registered route (allowlist: /docs,
      /redoc, /openapi.json)
- [ ] Full backend suite green; ruff + mypy clean
- [ ] PROJECT_STATUS queue updated (findings 1-5 closed)

## Files

| File | Action |
|------|--------|
| `backend/app/identity/service.py` | MODIFY — revoke all refresh on password change |
| `backend/app/identity/middleware.py` | MODIFY — PUBLIC_PATHS cleanup |
| `docs/security/auth-rbac.md` | REWRITE |
| `backend/tests/test_password_revoke_all.py` | CREATE (red→green) |
| `backend/tests/test_public_paths.py` | CREATE (regression) |
