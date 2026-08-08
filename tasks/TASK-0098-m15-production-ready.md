# TASK-0098: M15 — Production Ready

**Sprint:** M15 (5 sprints: S17.1–S17.5)
**Milestone:** M15 (0.17.0)
**Story Points:** ~60
**Status:** Planning
**Spec:** SPEC-0015

## Sprint Plan

### S17.1: Agent Workflow Core (2 weeks, ~15 pts)
- [ ] 7.1 Implement task claim endpoint (POST /tasks/{id}/claim)
- [ ] 7.2 Implement heartbeat endpoint (POST /tasks/{id}/heartbeat)
- [ ] 7.3 Implement stale claim detection (background job)
- [ ] 7.4 Add auth to agent endpoints (X-Agent-Token)

### S17.2: Clarification & Context (2 weeks, ~12 pts)
- [ ] 7.5 Implement clarification request (POST /tasks/{id}/clarifications)
- [ ] 7.6 Implement clarification answer (POST /clarifications/{id}/answer)
- [ ] 7.7 Implement context pack generator (GET /tasks/{id}/context-pack)

### S17.3: Evidence & DoD (2 weeks, ~14 pts)
- [ ] 8.1 Implement evidence attachment (POST /tasks/{id}/evidence)
- [ ] 8.2 Implement evidence verification (agent/human flow)
- [ ] 8.3 Implement DoD item management (CRUD)
- [ ] 8.4 Implement coverage calculation (GET /tasks/{id}/dod-coverage)

### S17.4: Review Rounds (2 weeks, ~12 pts)
- [ ] 8.5 Implement review round creation (POST /tasks/{id}/review-rounds)
- [ ] 8.6 Implement review verdict (POST /review-rounds/{id}/verdict)
- [ ] 8.7 Implement acceptance criteria (CRUD)

### S17.5: Notifications & Reports (2 weeks, ~10 pts)
- [ ] 9.1 Implement in-app notifications
- [ ] 9.2 Implement report generation
- [ ] 9.3 Implement dashboard stats API
- [ ] 9.4 Implement graceful shutdown

## Acceptance Criteria

- [ ] Agent can claim, heartbeat, release tasks
- [ ] Clarification flow works end-to-end
- [ ] Evidence can be attached and verified
- [ ] DoD coverage is calculated
- [ ] Review rounds work with findings and verdicts
- [ ] Notifications are created and displayed
- [ ] Reports can be generated
- [ ] All new endpoints have tests
- [ ] Frontend has unit tests
- [ ] E2e tests cover critical flows
- [ ] Pipeline passes

## Technical Notes

- Use existing models (task_claim, heartbeat, clarification_request, evidence, review_round, etc.)
- Build on existing auth middleware (M7)
- Use Redis for stale detection (M8)
- Keep MVP scope — email/webhook notifications in future
