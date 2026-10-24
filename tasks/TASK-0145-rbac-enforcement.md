# TASK-0145 — SPEC-0027 S27.1: RBAC enforcement (require_permission + Phase-A gates)

**Spec:** `specs/SPEC-0027-security-findings-closure.md` §3.1 (findings 1)
**Milestone:** SPEC-0027 (Этап 1)
**Points:** 8
**Status:** DONE (closed 2026-10-24)

## Objective

Runtime RBAC guard: FastAPI-dependency `require_permission(action, resource)`
on admin-dangerous mutations; Member PATCH project → 403 (not 404); writes
fail closed without identity; superusers bypass (spec amendment — replaces
backfill, see Deviations).

## Acceptance Criteria (verified 2026-10-24)

- [x] `backend/app/identity/permissions.py`: `require_permission` dependency —
      fail-closed order: `disable_auth` → inert; no identity → 401;
      unknown/inactive subject → **401** (defense in depth under finding 2);
      `is_superuser` → bypass; else RoleBinding → Role → RolePermission →
      Permission; no match → 403 + structured log + metric + span attrs
- [x] Redis cache `rbac:user_perms:{user_id}` TTL 60s; Redis/miss → DB query
      (graceful degradation, rate-limiter pattern)
- [x] Phase-A gates: `POST/PATCH/DELETE /api/v1/projects` →
      create/update/delete:project; agent mutations (create/token/revoke) →
      manage:agent. *user-management gates: N/A — no user-mgmt endpoints
      exist (only self-service `/auth/password/change`, correctly ungated)*
- [x] **Red first:** hermetic suite `test_rbac_enforcement.py` — red
      (6 failed → revised design red: 3 failed) → green **11/11**
- [x] Read-regression: member GET 200 + `disable_auth=true` gates inert test
      (existing open-client suites unaffected)
- [x] Positive controls: Owner (binding) mutations pass; superuser WITHOUT
      binding bypasses (seeder/setup admin shape)
- [x] Live authz suite: `test_member_update_project_enforces_role` — xfail
      **removed, strict pass**; full run: **53 passed, 1 skipped,
      2 xfailed** (remaining xfails = findings 2/3, TASK-0146/0147)
- [x] Full backend suite: **979 passed** (3 pre-existing `test_redis`
      failures = local env missing `redis` pkg, baseline-confirmed via
      stash; `test_cli.py` pre-existing local `typer` gap — both declared
      in `backend/requirements.txt`, installed in CI)
- [x] `ruff check` + `ruff format` clean; `mypy backend/app` clean
      (113 files, .venv/bin/mypy)
- [x] Structured logging on denials (JSONFormatter: `action`,
      `entity_type=rbac_gate`), `upcp_rbac_denials_total` metric,
      OTel span attributes `upcp.rbac.*`

## Deviations (recorded per §7)

1. **Backfill → superuser-bypass (spec amended).** Blanket
   Owner-backfill would also promote the deliberately permission-less
   seeder agent users and destroy the authz negative control for
   finding 1. Bypass mirrors existing `_require_agent` admin check;
   no migration needed (only user-creation path is `/auth/setup`, which
   already creates superuser + Owner binding). Rejected alternative
   recorded in SPEC-0027 §3.1/AC9 (amended 2026-10-24).
2. **`disable_auth` short-circuit.** Gates are inert under
   `UPCP_DISABLE_AUTH=true` (hermetic conftest) — consistent with
   main.py not mounting AuthMiddleware then; keeps ~900 existing
   open-client tests untouched without overrides.
3. **Latent test bug fixed en route:** `test_security_hardening.py`
   cleared the `get_settings()` lru_cache *inside*
   `patch.dict(UPCP_DISABLE_AUTH=...)` but never after — the patched
   snapshot leaked to later tests and turned `test_structure` red once
   gates consulted `disable_auth` per request. Fixed with autouse
   cache-reset fixture (root cause, not test-by-test patching).

## Evidence

- Local: targeted pytest RBAC **11/11**; full backend **979 passed**
  (3 pre-existing redis-env failures, baseline-verified via
  `git stash` run); ruff/format clean; `mypy backend/app` **no issues
  in 113 files**
- Live test stack (compose up → seeder → suite → stop):
  authz suite **53 passed / 1 skipped / 2 xfailed** — finding 1 strict;
  findings 2/3 xfail remain until TASK-0146/0147
- Stack env gotcha hit & fixed: shell-inherited dev ports
  (`UPCP_PORT_POSTGRES=35432`) overrode `--env-file .env.test` →
  explicit `UPCP_PORT_POSTGRES=35434 UPCP_PORT_BACKEND=38082` overrides
  + `SECURITY_DB_PORT=35434` for the member-identity DB lookup

## Files

| File | Action |
|------|--------|
| `backend/app/identity/permissions.py` | CREATE — gate + cache + bypass |
| `backend/app/api/v1/projects.py` | MODIFY — 3 route gates |
| `backend/app/identity/agent_endpoints.py` | MODIFY — 3 route gates |
| `backend/app/shared/metrics.py` | MODIFY — `upcp_rbac_denials_total` |
| `backend/tests/test_rbac_enforcement.py` | CREATE (red→green, 11 tests) |
| `backend/tests/test_security_hardening.py` | FIX — settings-cache leak |
| `tests/security/authz/test_rbac.py` | MODIFY — xfail removed (finding 1) |
| `specs/SPEC-0027-security-findings-closure.md` | AMEND §3.1/AC9 |
