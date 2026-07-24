# TASK-0013 Git Read Integration

Spec: SPEC-0011
Status: done
Priority: 10
Model: routine
Milestone: M3

## Goal

Implement gitread context with config, models, local adapter, and linking.

## Files likely involved

```text
backend/app/gitread/__init__.py
backend/app/gitread/models.py
backend/app/gitread/schemas.py
backend/app/gitread/service.py
backend/app/gitread/adapters.py
backend/app/api/v1/gitread.py
backend/tests/test_gitread.py
backend/alembic/versions/0009_add_gitread.py
```

## Acceptance Criteria

- GitProvider CRUD.
- LocalGitAdapter reads branches/commits.
- GitLink CRUD.
- Coverage >= 80%.

## DoD

- tests added;
- implementation added;
- migration generated;
- commands pass;
- statuses updated.
