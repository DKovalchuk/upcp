# TASK-0073 Task Dependencies

Spec: SPEC-0014
Status: done
Priority: 8
Model: routine
Milestone: M9

## Goal

Track task blocking relationships.

## Files likely involved

```text
backend/app/delivery/models.py          # add TaskDependency
backend/app/delivery/schemas.py         # add dependency schemas
backend/app/delivery/service.py         # add dependency checks
backend/alembic/versions/0014_*.py      # migration
backend/tests/test_delivery.py          # tests
```

## Acceptance Criteria

- [ ] TaskDependency model (id, task_id, blocked_by_task_id, created_at).
- [ ] Unique constraint on (task_id, blocked_by_task_id).
- [ ] No self-dependency.
- [ ] No circular dependency detection (BFS/DFS).
- [ ] Migration created and applies cleanly.
- [ ] Tests cover creation, uniqueness, cycle detection.

## DoD

- tests added and passing;
- implementation complete;
- migration applies;
- commands pass;
- status updated.
