# TASK-0145 — SPEC-0027 S27.1: RBAC enforcement (require_permission + Phase-A gates)

**Spec:** `specs/SPEC-0027-security-findings-closure.md` §3.1 (findings 1)
**Milestone:** SPEC-0027 (Этап 1)
**Points:** 8
**Status:** PENDING

## Objective

Runtime RBAC guard: FastAPI-dependency `require_permission(action, resource)`
on admin-dangerous mutations; Member PATCH project → 403 (not 404);
backfill Owner bindings for existing binding-less users.

## Acceptance Criteria

- [ ] `backend/app/identity/permissions.py`: `require_permission` dependency —
      resolves `request.state.user_id` → RoleBinding(global+org) →
      Role → RolePermission → Permission; no match → 403; no user_id → 401
- [ ] Redis cache `rbac:user_perms:{user_id}` TTL 60s; Redis/miss → DB query;
      Redis down → DB query (no fail-open needed — DB is source of truth here)
- [ ] Phase-A gates: `POST/PATCH/DELETE /api/v1/projects` → create/update/delete:project;
      agent mutations (create/token/revoke/delete) → manage:agent;
      user mutations → manage:user
- [ ] Backfill: idempotent — every `user_account` without binding gets Owner
- [ ] **Red first:** unit test Member PATCH project → 403 (xfail-эквивалент
      в hermetic TestClient), Owner → 200; write test → run (fail) → implement → pass
- [ ] Read-regression test: GET domain endpoints unchanged for any-authenticated
- [ ] Live authz suite: `test_member_update_project_enforces_role` — xfail removed, strict pass
- [ ] Full backend suite green; ruff + mypy clean
- [ ] Structured logging on 403 denials (user_id, action, resource)

## Files

| File | Action |
|------|--------|
| `backend/app/identity/permissions.py` | CREATE |
| `backend/app/api/v1/projects.py` | MODIFY — gates |
| `backend/app/identity/agent_endpoints.py` | MODIFY — manage:agent gates |
| `backend/app/identity/seed.py` or migration | MODIFY — backfill |
| `backend/tests/test_rbac_enforcement.py` | CREATE (red→green) |
| `tests/security/authz/test_rbac.py` | MODIFY — remove xfail |
