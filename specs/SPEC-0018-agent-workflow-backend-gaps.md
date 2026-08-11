# SPEC-0018: Agent Workflow Backend Gaps

**Version:** 1.0
**Date:** 2026-08-11
**Status:** Draft
**Milestone:** M15 Sprint 1 (S17.1)
**Parent:** SPEC-0017 (M15 Production Ready)
**Related tasks:** TASK-0099

## 1. Objective

Close all backend gaps in the Agent Workflow layer so that frontend can build full UI in subsequent sprints. The backend for M9–M11 models and basic endpoints exist, but 7 critical gaps prevent a complete agent workflow experience.

## 2. Gaps Summary

| ID | Gap | Impact | Priority |
|----|-----|--------|----------|
| B1 | No REST endpoints for clarification create/answer | Agents can only use MCP, no HTTP flow | High |
| B2 | No stale claim reaper | Dead claims never auto-released | High |
| B3 | Agent inbox is a stub (empty events) | No event feed for agents | Medium |
| B4 | Lifecycle not enforced on PATCH /tasks/:id | Status can bypass state machine | Medium |
| B5 | No agent metrics endpoint | Agent detail page has no data | High |
| B6 | No agent detail endpoints (claims, activity, evidence, reviews, clarifications) | Agent detail page impossible | High |
| B7 | Task dependency CRUD endpoints missing | No API to manage dependencies | Low |

## 3. Architecture

### 3.1 New Model: AgentInboxEvent

```python
class AgentInboxEvent(Base):
    __tablename__ = "agent_inbox_event"

    id: str              # UUID
    agent_id: str        # FK to agent (denormalized, no FK for perf)
    event_type: str      # "clarification_request" | "claim_released" | "review_assigned" | "status_change" | "heartbeat_stale"
    task_id: str | None  # Related task (nullable for system events)
    message: str         # Human-readable message
    metadata_json: str | None  # Extra data (JSON string)
    is_read: bool        # Default False
    created_at: datetime
```

Indexes:
- `ix_agent_inbox_event_agent_id` on `agent_id`
- `ix_agent_inbox_event_created_at` on `created_at`

### 3.2 Clarification Service

New service methods in `WorkflowService`:

```python
def create_clarification(
    self, task_id: str, *, agent_id: str,
    question: str, context: str | None = None, blocking: bool = False
) -> ClarificationRequest:
    # 1. Validate task exists
    # 2. Validate agent has active claim on task
    # 3. Create ClarificationRequest (author_type="agent", author_id=agent_id)
    # 4. If blocking: validate_transition → needs_clarification
    # 5. Create AgentInboxEvent for task owner
    # 6. flush

def answer_clarification(
    self, clarification_id: str, *, answered_by: str, answer: str
) -> ClarificationRequest:
    # 1. Validate clarification exists, state == "open"
    # 2. Set answer, answered_by, answered_at, state="answered"
    # 3. If was blocking: validate_transition task → in_progress
    # 4. Create AgentInboxEvent for clarification author
    # 5. flush

def resolve_clarification(self, clarification_id: str) -> ClarificationRequest:
    # 1. Validate exists, state == "answered"
    # 2. Set state = "resolved"
    # 3. flush
```

### 3.3 Stale Claim Reaper

**Constants:**
```python
STALE_MINUTES = 5    # Heartbeat older than this → stale notification
DEAD_MINUTES = 15    # Heartbeat older than this → auto-release
```

**Background task (asyncio):**
```python
async def stale_reaper_loop(session_factory, interval_seconds=60):
    while True:
        await asyncio.sleep(interval_seconds)
        with session_factory() as session:
            reaper_tick(session)
```

**REST endpoint (for k8s probes / external schedulers):**
```python
POST /internal/reaper/tick
# Returns: { "stale": N, "released": N }
```

**Logic:**
1. Find active claims where `last_heartbeat_at < now - STALE_MINUTES` → create `AgentInboxEvent` with type `heartbeat_stale`
2. Find active claims where `last_heartbeat_at < now - DEAD_MINUTES` (or never heartbeated, `claimed_at < now - DEAD_MINUTES`) → release claim, task → backlog, create event

### 3.4 Lifecycle Enforcement

In `TaskService.update()`:
```python
def update(self, task_id, **fields):
    t = self.get(task_id)
    new_status = fields.get("status")
    if new_status is not None and new_status != t.status:
        from app.delivery.lifecycle import validate_transition
        validate_transition(t.status, new_status)
    # ... existing setattr logic
```

### 3.5 Agent Metrics

Enhanced `GET /agents/{id}` response:

```json
{
    "id": "...",
    "name": "...",
    "is_active": true,
    "metrics": {
        "tasks_completed": 12,
        "tasks_failed": 1,
        "success_rate": 92.3,
        "current_task_id": "...",
        "current_task_title": "...",
        "current_progress_percent": 67,
        "last_heartbeat_at": "...",
        "is_stale": false,
        "status": "working"
    }
}
```

**Status calculation:**
- `working`: has active claim AND last_heartbeat < 5 min
- `idle`: no active claims
- `stale`: has active claim AND last_heartbeat > 5 min
- `offline`: no active claims AND last activity > 1 hour

### 3.6 Agent Detail Endpoints

```
GET /agents/:id/claims          → [{ id, task_id, task_title, state, claimed_at, released_at, duration }]
GET /agents/:id/activity        → [{ id, event_type, task_id, message, created_at }]
GET /agents/:id/evidence        → [{ id, task_id, type, title, verification_state, created_at }]
GET /agents/:id/reviews         → [{ id, task_id, state, verdict, confidence, created_at }]
GET /agents/:id/clarifications  → [{ id, task_id, question, state, blocking, created_at }]
```

### 3.7 Task Dependency CRUD (Low Priority)

```
POST   /tasks/:id/dependencies          → create dependency
DELETE /tasks/:id/dependencies/:dep_id  → remove dependency
GET    /tasks/:id/dependencies          → list dependencies
```

Validation: cycle detection via existing `detect_cycle()`, no self-dependency.

## 4. API Contracts

### Clarification

```yaml
POST /api/v1/tasks/{task_id}/clarifications:
  summary: Create clarification request
  auth: X-Agent-Token
  body:
    question: str (required)
    context: str | null
    blocking: bool (default false)
  response 201: { id, task_id, state, question, blocking, created_at }
  errors: 404 (task not found), 409 (no active claim)

POST /api/v1/clarifications/{clarification_id}/answer:
  summary: Answer clarification request
  auth: X-Agent-Token
  body:
    answer: str (required)
  response 200: { id, state, answer, answered_at }
  errors: 404 (not found), 409 (already answered)
```

### Stale Reaper

```yaml
POST /api/v1/internal/reaper/tick:
  summary: Trigger stale claim check
  auth: internal (no auth required in test, API key in prod)
  response 200: { stale: int, released: int }
```

### Agent Metrics

```yaml
GET /api/v1/agents/{agent_id}:
  summary: Get agent with metrics
  auth: JWT (current user)
  response 200: { id, name, is_active, metrics: {...}, tokens: [...] }
```

### Agent Detail

```yaml
GET /api/v1/agents/{agent_id}/claims:
GET /api/v1/agents/{agent_id}/activity:
GET /api/v1/agents/{agent_id}/evidence:
GET /api/v1/agents/{agent_id}/reviews:
GET /api/v1/agents/{agent_id}/clarifications:
  auth: JWT (current user)
  response 200: { items: [...] }
```

## 5. Database Changes

New table: `agent_inbox_event`
- Migration: `0018_add_agent_inbox_events.py`

## 6. Non-goals

- Real-time WebSocket events (future)
- Email/webhook notifications (future)
- Agent-to-agent messaging (future)
- Per-project playbook storage (future)

## 7. Acceptance Criteria

- [ ] `POST /tasks/{id}/clarifications` creates clarification, blocks task if blocking
- [ ] `POST /clarifications/{id}/answer` answers clarification, unblocks task
- [ ] Stale claim reaper releases dead claims after 15 min
- [ ] Agent inbox events generated on claim, clarification, review, stale
- [ ] `PATCH /tasks/{id}` with status change validates lifecycle transitions
- [ ] `GET /agents/:id` returns metrics (tasks_completed, success_rate, is_stale, status)
- [ ] Agent detail endpoints return claim history, activity, evidence, reviews, clarifications
- [ ] All endpoints have unit + integration tests
- [ ] Coverage > 80% for new code
