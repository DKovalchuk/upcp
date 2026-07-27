# TASK-0065 RBAC Models

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M7

## Goal

RBAC models: Role, Permission, RoleBinding with proper constraints and indexes.

## Files likely involved

```text
backend/app/identity/rbac.py            # new
backend/tests/test_rbac.py              # new
```

## Acceptance Criteria

- [ ] Role model (name, scope).
- [ ] Permission model (action, resource).
- [ ] RolePermission association table.
- [ ] RoleBinding model (user, role, org?, project?).
- [ ] Proper indexes on all FK columns.
- [ ] Unique constraints where needed.
- [ ] Tests for all models.
- [ ] Migration generated.
- [ ] Commands pass.

## DoD

- tests added and passing;
- implementation complete;
- migration generated;
- commands pass;
- status updated.
