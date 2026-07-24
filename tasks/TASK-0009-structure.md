# TASK-0009 Component + Module CRUD

Spec: SPEC-0008
Status: done
Priority: 10
Model: routine
Milestone: M2

## Goal

Implement Component and Module entities with CRUD.

## Non-goals

- No delivery entities.

## Files likely involved

```text
backend/app/structure/__init__.py
backend/app/structure/models.py
backend/app/structure/schemas.py
backend/app/structure/service.py
backend/app/api/v1/structure.py
backend/tests/test_structure.py
backend/alembic/versions/0005_add_structure.py
```

## Acceptance Criteria

- Component CRUD under project.
- Module CRUD under component.
- Slug uniqueness within parent.
- Coverage >= 80%.

## DoD

- tests added;
- implementation added;
- migration generated;
- commands pass;
- statuses updated.
