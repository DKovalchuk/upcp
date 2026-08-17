# TASK-0099: Agent Workflow Backend Gaps

**Sprint:** M15 S17.1
**Milestone:** M15 (0.17.0)
**Spec:** SPEC-0018
**Status:** in_progress
**Story Points:** ~15

## Subtasks

### B1: Clarification REST Endpoints
- [ ] Unit tests for `WorkflowService.create_clarification()`
- [ ] Unit tests for `WorkflowService.answer_clarification()`
- [ ] Unit tests for `WorkflowService.resolve_clarification()`
- [ ] Implement `create_clarification()` in `workflow.py`
- [ ] Implement `answer_clarification()` in `workflow.py`
- [ ] Implement `resolve_clarification()` in `workflow.py`
- [ ] `POST /tasks/{id}/clarifications` endpoint
- [ ] `POST /clarifications/{id}/answer` endpoint
- [ ] Integration tests for both endpoints

### B2: Stale Claim Reaper
- [ ] Unit tests for `reaper_tick()`
- [ ] Unit tests for stale notification generation
- [ ] Unit tests for dead claim auto-release
- [ ] Implement `reaper_tick()` in `stale_reaper.py`
- [ ] Implement `stale_reaper_loop()` async background task
- [ ] `POST /internal/reaper/tick` endpoint
- [ ] Register startup event in `main.py`
- [ ] Integration tests for reaper endpoint

### B3: Agent Inbox Events
- [ ] `AgentInboxEvent` model
- [ ] Migration 0018
- [ ] Unit tests for `create_agent_event()`
- [ ] Unit tests for `get_agent_events()`
- [ ] Implement `create_agent_event()` in `inbox_events.py`
- [ ] Implement `get_agent_events()` in `inbox_events.py`
- [ ] Wire events into claim, clarification, review flows
- [ ] Integration tests

### B4: Lifecycle Enforcement
- [ ] Unit tests for `TaskService.update()` with status change
- [ ] Unit tests: valid transition passes, invalid raises
- [ ] Implement lifecycle check in `TaskService.update()`
- [ ] Integration tests: PATCH with valid/invalid status

### B5: Agent Metrics Endpoint
- [ ] Unit tests for metrics calculation
- [ ] Enhance `GET /agents/{id}` with metrics fields
- [ ] Unit tests for status calculation (working/idle/stale/offline)
- [ ] Integration tests

### B6: Agent Detail Endpoints
- [ ] Unit tests for each endpoint
- [ ] `GET /agents/:id/claims`
- [ ] `GET /agents/:id/activity`
- [ ] `GET /agents/:id/evidence`
- [ ] `GET /agents/:id/reviews`
- [ ] `GET /agents/:id/clarifications`
- [ ] Integration tests for each endpoint

### B7: Task Dependency CRUD
- [ ] `POST /tasks/:id/dependencies`
- [ ] `DELETE /tasks/:id/dependencies/:dep_id`
- [ ] `GET /tasks/:id/dependencies`
- [ ] Cycle detection validation
- [ ] Tests

## Acceptance Criteria

- [ ] All clarification endpoints work with X-Agent-Token auth
- [ ] Stale reaper releases claims after 15 min dead
- [ ] Agent inbox events appear on workflow actions
- [ ] PATCH /tasks/:id enforces lifecycle state machine
- [ ] GET /agents/:id returns metrics
- [ ] Agent detail endpoints return related data
- [ ] All tests pass
- [ ] Coverage > 80%

## Files to Create

- `specs/SPEC-0018-agent-workflow-backend-gaps.md` ✅
- `backend/app/delivery/stale_reaper.py`
- `backend/app/delivery/inbox_events.py`
- `backend/alembic/versions/0018_add_agent_inbox_events.py`
- `backend/tests/test_clarification_service.py`
- `backend/tests/test_clarification_api.py`
- `backend/tests/test_stale_reaper.py`
- `backend/tests/test_agent_detail.py`
- `backend/tests/test_lifecycle_enforcement.py`
- `backend/tests/test_inbox_events.py`

## Files to Modify

- `backend/app/delivery/workflow.py` — +3 methods
- `backend/app/delivery/service.py` — lifecycle enforcement
- `backend/app/delivery/models.py` — +AgentInboxEvent
- `backend/app/api/v1/task_workflow.py` — +2 endpoints
- `backend/app/identity/agent_endpoints.py` — +metrics, +5 detail endpoints
- `backend/app/main.py` — +reaper startup, +reaper router
