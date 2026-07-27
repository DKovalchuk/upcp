# TASK-0071 ClarificationRequest Model

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M9

## Goal

Model for agent clarification requests during task execution.

## Files likely involved

```text
backend/app/delivery/models.py          # add ClarificationRequest
backend/app/delivery/schemas.py         # add clarification schemas
backend/alembic/versions/0013_*.py      # migration
backend/tests/test_delivery.py          # tests
```

## Acceptance Criteria

- [ ] ClarificationRequest model (id, task_id, author_type, author_id, question, context, blocking, state, answer, answered_by, answered_at, created_at).
- [ ] State enum: open, answered, resolved.
- [ ] blocking flag controls whether task pauses.
- [ ] Migration created and applies cleanly.
- [ ] Tests cover creation, answering, resolving.

## DoD

- tests added and passing;
- implementation complete;
- migration applies;
- commands pass;
- status updated.
