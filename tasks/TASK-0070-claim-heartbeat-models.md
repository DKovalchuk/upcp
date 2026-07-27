# TASK-0070 TaskClaim + Heartbeat Models

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M9

## Goal

Models for agent task claiming and heartbeat tracking.

## Files likely involved

```text
backend/app/delivery/models.py          # add TaskClaim, Heartbeat
backend/app/delivery/schemas.py         # add claim/heartbeat schemas
backend/alembic/versions/0012_*.py      # migration
backend/tests/test_delivery.py          # tests
```

## Acceptance Criteria

- [ ] TaskClaim model (id, task_id, agent_id, state, claimed_at, released_at, expires_at, last_heartbeat_at, context_snapshot).
- [ ] Heartbeat model (id, claim_id, progress_percent, current_step, next_step, blockers, eta, created_at).
- [ ] Claim state enum: active, released, expired, completed.
- [ ] Unique constraint: only one active claim per task.
- [ ] Migration created and applies cleanly.
- [ ] Tests cover creation, unique constraint, state transitions.

## DoD

- tests added and passing;
- implementation complete;
- migration applies;
- commands pass;
- status updated.
