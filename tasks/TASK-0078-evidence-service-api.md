# TASK-0078 Evidence Service + API

Status: pending
Milestone: M10
Spec: SPEC-0015
Depends: TASK-0077

## Goal

Evidence CRUD service and API endpoints.

## Acceptance Criteria

- EvidenceService: create, get, list_by_task, verify, accept, reject.
- State transitions enforced (unverified → agent_verified → human_accepted/rejected).
- API: GET /tasks/{id}/evidence, POST /tasks/{id}/evidence, POST /evidence/{id}/agent-verify, POST /evidence/{id}/human-accept, POST /evidence/{id}/reject.
- Error responses per SPEC-0015 format.
- Tests for all endpoints and state transitions.
