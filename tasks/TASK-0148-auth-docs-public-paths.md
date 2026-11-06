# TASK-0148 — SPEC-0027 S27.4: Password-change revocation + docs rewrite + PUBLIC_PATHS

**Spec:** `specs/SPEC-0027-security-findings-closure.md` §3.4 (findings 4-5)
**Milestone:** SPEC-0027 (Этап 1)
**Points:** 3
**Status:** DONE (closed 2026-10-24)
**Depends on:** TASK-0145 (docs must document its gates)

## Objective

Close doc-code mismatch honestly: implement promised refresh-revocation on
password change, rewrite `docs/security/auth-rbac.md` to actual behavior,
remove dead `/mcp/health` from PUBLIC_PATHS.

## Acceptance Criteria (verified 2026-10-24)

- [x] **Red first:** `change_password` success → ALL user's refresh tokens
      revoked — red (`Failed: DID NOT RAISE ValueError`) → green **2/2**
      (`test_password_revoke_all.py`; refused change revokes nothing)
- [x] Access JWTs of other sessions stay valid until exp — documented as
      limitation (docs §8 EN/RU; needs a jti claim to enforce earlier)
- [x] `docs/security/auth-rbac.md` rewritten: paths `/auth/*` (не
      `/api/v1/auth/*`), actual claims `sub/type/iat/exp` (нет jti,
      roles/scopes), denylist + Redis-degradation note, password-change
      semantics, `require_permission` usage example; **+ RU-локализация**
      `auth-rbac.ru.md` (bilingual-nav feedback: языковой переключатель,
      TOC-якоря, cross-ссылки, без копирайта)
- [x] Doc-literal test: `` `METHOD /path` `` in docs == OpenAPI routes
      (`test_public_paths.py::test_auth_docs_paths_match_code_routes`)
- [x] `/mcp/health` removed from `PUBLIC_PATHS`; regression test: every
      PUBLIC_PATHS entry resolves to registered route (allowlist: /docs,
      /redoc, /openapi.json) — red `['/mcp/health']` → green
- [x] Full backend suite green (**993 passed**, 3 pre-existing
      `test_redis`); ruff check/format clean; `mypy backend/app` no issues
      (114 files)
- [x] PROJECT_STATUS updated (findings 1-5 closed)

## Evidence

- Red→green: revoke **DID NOT RAISE → 2/2**; PUBLIC_PATHS regression
  **['/mcp/health'] → green**; doc-literal **empty set → green**
- Full backend: **993 passed / 3 failed** (all 3 = pre-existing redis-env,
  baseline from TASK-0145)
- Live stack (compose up → seeder → suite → stop): authz **55 passed /
  1 skipped / 0 xfailed** — no regressions from PUBLIC_PATHS/password
  changes (live password tests are negative-path only)
- FastAPI 0.138.0 finding: `app.routes` exposes lazy `_IncludedRouter`
  wrappers (no `.path`) — the regression test enumerates routes via
  `app.openapi()["paths"]` (public API, 101 paths)

## Deviations / factual fixes beyond the AC list

1. **Bilingual expansion** (feedback «Bilingual documentation»): the
   rewrite landed as EN + RU files with language switcher/TOC/related
   links — the AC named only the EN file.
2. **Other doc lies fixed en route**: lockout 15→**30 min**
   (`LOCKOUT_MINUTES`), setup conflict 410→**409**, refresh returned in
   **JSON body** (not httpOnly cookie), password min length 8 (not 12),
   nonexistent `/auth/password/reset/*` endpoints removed, audit action
   names aligned (`login_success`…), reuse → 401 without family revocation
   (documented as limitation).
3. **Suite README synced**: xfail-findings section → "all closed" map
   (TASK-0145..0148), coverage-matrix cells updated, `/mcp/health`
   limitation bullet replaced.

## Files

| File | Action |
|------|--------|
| `backend/app/identity/service.py` | MODIFY — revoke all refresh on password change |
| `backend/app/identity/middleware.py` | MODIFY — PUBLIC_PATHS cleanup |
| `docs/security/auth-rbac.md` | REWRITE (EN) |
| `docs/security/auth-rbac.ru.md` | CREATE (RU, bilingual nav) |
| `backend/tests/test_password_revoke_all.py` | CREATE (red→green) |
| `backend/tests/test_public_paths.py` | CREATE (regression + doc-literal) |
| `backend/tests/test_auth_middleware_protection.py` | MODIFY — /mcp/health now 401 |
| `tests/security/authz/README.md` | SYNC — findings closed |
