# TASK-0011+0012 Acceptance Criteria, DoD, Quality Gate

Spec: SPEC-0010
Status: done
Priority: 10
Model: routine
Milestone: M2

## Goal

Add quality context with acceptance criteria, DoD items, and quality gate.

## Files likely involved

```text
backend/app/quality/__init__.py
backend/app/quality/models.py
backend/app/quality/schemas.py
backend/app/quality/service.py
backend/app/api/v1/quality.py
backend/tests/test_quality.py
backend/alembic/versions/0007_add_quality.py
```

## Acceptance Criteria

- AcceptanceCriterion CRUD.
- DoDItem CRUD.
- Quality gate: task done only if all DoD passed.
- Coverage >= 80%.

## DoD

- tests added;
- implementation added;
- migration generated;
- commands pass;
- statuses updated.
