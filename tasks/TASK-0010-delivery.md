# TASK-0010 Feature, Task, Subtask CRUD

Spec: SPEC-0009
Status: done
Priority: 10
Model: routine
Milestone: M2

## Goal

Implement Feature, Task, Subtask entities with CRUD.

## Files likely involved

```text
backend/app/delivery/__init__.py
backend/app/delivery/models.py
backend/app/delivery/schemas.py
backend/app/delivery/service.py
backend/app/api/v1/delivery.py
backend/tests/test_delivery.py
backend/alembic/versions/0006_add_delivery.py
```

## Acceptance Criteria

- Feature CRUD under project.
- Task CRUD under feature.
- Subtask CRUD under task.
- Coverage >= 80%.

## DoD

- tests added;
- implementation added;
- migration generated;
- commands pass;
- statuses updated.
