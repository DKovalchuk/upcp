# TASK-0062 User Model and Migration

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M7

## Goal

Add User model with email/password authentication and Organization + Membership models for multi-org readiness.

## Non-goals

- No auth middleware yet (TASK-0065).
- No JWT service yet (TASK-0064).
- No RBAC yet (TASK-0066).
- No agent model yet (TASK-0068).

## Files likely involved

```text
backend/app/identity/models.py          # new
backend/app/identity/schemas.py         # new
backend/app/identity/__init__.py        # new
backend/tests/identity/__init__.py      # new
backend/tests/identity/test_models.py   # new
```

## TDD Steps

1. Create failing tests for User model:
   - User can be created with email, password_hash, display_name.
   - User email must be unique.
   - User has is_active (default True) and is_superuser (default False).
   - User has created_at and updated_at timestamps.
   - User can be queried by email.
   - User password_hash is never the raw password.

2. Create failing tests for Organization model:
   - Organization can be created with name and slug.
   - Organization slug must be unique.
   - Organization has is_default (default False).
   - Organization has created_at timestamp.

3. Create failing tests for Membership model:
   - Membership links User ↔ Organization.
   - Membership has role field (owner, admin, member, viewer).
   - Composite unique constraint on (user_id, org_id).

4. Run tests, confirm all fail.

5. Implement User model:
   - id: String(36), PK, default=new_id
   - email: String(255), unique, not null
   - password_hash: String(255), not null
   - display_name: String(255), not null
   - is_active: Boolean, default=True
   - is_superuser: Boolean, default=False
   - created_at: DateTime(timezone=True), default=utcnow
   - updated_at: DateTime(timezone=True), default=utcnow, onupdate=utcnow

6. Implement Organization model:
   - id: String(36), PK, default=new_id
   - name: String(255), not null
   - slug: String(255), unique, not null
   - is_default: Boolean, default=False
   - created_at: DateTime(timezone=True), default=utcnow

7. Implement Membership model:
   - id: String(36), PK, default=new_id
   - user_id: String(36), FK → user.id, not null
   - org_id: String(36), FK → organization.id, not null
   - role: String(50), not null (owner/admin/member/viewer)
   - created_at: DateTime(timezone=True), default=utcnow
   - UniqueConstraint(user_id, org_id)

8. Create Pydantic schemas for User, Organization, Membership.

9. Run tests, confirm all pass.

10. Generate Alembic migration.

11. Run `make lint` and `make typecheck`.

## Acceptance Criteria

- [ ] User model created with all fields.
- [ ] Organization model created with all fields.
- [ ] Membership model created with FK constraints and unique constraint.
- [ ] Pydantic schemas for all three models.
- [ ] Tests cover creation, unique constraints, defaults, timestamps.
- [ ] Alembic migration generated and applies cleanly.
- [ ] `make test` passes.
- [ ] `make lint` passes.
- [ ] `make typecheck` passes.
- [ ] Status updated to done.

## DoD

- tests added and passing;
- models implemented;
- migration generated;
- schemas created;
- commands pass;
- status updated.
