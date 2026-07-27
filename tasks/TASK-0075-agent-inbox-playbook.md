# TASK-0075 Agent Inbox + Playbook

Spec: SPEC-0014
Status: done
Priority: 8
Model: routine
Milestone: M9

## Goal

Agent self-service endpoints: inbox (events/notifications) and playbook.

## Dependencies

- TASK-0074 (agent workflow endpoints)

## Files likely involved

```text
backend/app/api/v1/agent_self.py        # new — agent self-service router
backend/app/identity/agent_service.py   # new — inbox + playbook logic
backend/app/api/v1/__init__.py          # register router
backend/tests/test_agent_self.py        # new
```

## API Endpoints

```yaml
GET /agent/me
  # Agent self-service. Auth via X-Agent-Token.
  Response: { agent, scopes, assignments, inbox_count }

GET /agent/inbox?since=<ISO timestamp>
  Response: { events: [AgentEvent] }

GET /agent/playbook
  Response: markdown (agent playbook content)
```

## AgentEvent structure

```json
{
  "id": "evt-001",
  "type": "clarification_requested|task_assigned|review_complete|status_change",
  "task_id": "task-001",
  "message": "Human requested clarification on task",
  "created_at": "2026-07-27T10:00:00Z"
}
```

## Acceptance Criteria

- [ ] GET /agent/me returns agent profile, scopes, project assignments, inbox count.
- [ ] GET /agent/inbox returns events since timestamp, sorted by created_at desc.
- [ ] GET /agent/playbook returns markdown playbook content.
- [ ] Agent auth via X-Agent-Token header.
- [ ] Inbox events generated on: claim, clarification requested, review complete, status change.
- [ ] Tests cover all endpoints, filtering, auth.

## DoD

- tests added and passing;
- implementation complete;
- commands pass;
- status updated.
