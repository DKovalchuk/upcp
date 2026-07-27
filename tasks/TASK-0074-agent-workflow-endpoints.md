# TASK-0074 Agent Workflow Endpoints

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M9

## Goal

REST API endpoints for agent task workflow: claim, release, heartbeat, progress.

## Dependencies

- TASK-0070 (TaskClaim + Heartbeat models)
- TASK-0072 (lifecycle state machine)

## Files likely involved

```text
backend/app/delivery/workflow.py        # new — WorkflowService
backend/app/api/v1/task_workflow.py     # new — router
backend/app/api/v1/__init__.py          # register router
backend/app/delivery/schemas.py         # workflow request/response schemas
backend/tests/test_workflow.py          # new
```

## API Endpoints

```yaml
POST /tasks/{id}/claim
  Request: { context_snapshot?: str }
  Response: TaskClaim
  Errors: TASK_ALREADY_CLAIMED, TASK_NOT_READY, FORBIDDEN

POST /tasks/{id}/release
  Response: { ok: true }
  Errors: TASK_NOT_CLAIMED_BY_YOU

POST /tasks/{id}/heartbeat
  Request: { progress_percent: int, current_step: str, next_step: str, blockers?: str, eta?: str }
  Response: { ok: true }

POST /tasks/{id}/progress
  Request: { progress_percent: int, message?: str }
  Response: { ok: true }
```

## Acceptance Criteria

- [ ] POST /tasks/{id}/claim — creates active claim, updates task status.
- [ ] POST /tasks/{id}/release — releases claim, reverts task to backlog/ready.
- [ ] POST /tasks/{id}/heartbeat — updates last_heartbeat_at, creates Heartbeat record.
- [ ] POST /tasks/{id}/progress — updates progress_percent, creates Heartbeat record.
- [ ] Claim checks: task must be ready, not already claimed.
- [ ] Release checks: claim must belong to the requesting agent.
- [ ] Agent auth via X-Agent-Token header.
- [ ] Tests cover all endpoints, error cases, auth.

## DoD

- tests added and passing;
- implementation complete;
- commands pass;
- status updated.
