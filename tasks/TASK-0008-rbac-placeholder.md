# TASK-0008 RBAC Placeholder

Spec: SPEC-0007
Status: done
Priority: 10
Model: pro
Milestone: M1

## Goal

Add User, Role, Permission models and current_user dependency.

## Non-goals

- No real auth.
- No permission enforcement.

## Files likely involved

```text
backend/app/shared/auth.py
backend/tests/test_auth.py
backend/alembic/versions/0004_add_rbac.py
```

## TDD Steps

1. Create failing tests.
2. Implement models and dependency.
3. Generate migration.
4. Run tests, lint, typecheck.

## Acceptance Criteria

- User, Role, Permission models exist.
- Association tables exist.
- current_user returns placeholder.
- Migration generated.
- Coverage >= 80%.

## DoD

- tests added;
- implementation added;
- migration generated;
- commands pass;
- statuses updated.
