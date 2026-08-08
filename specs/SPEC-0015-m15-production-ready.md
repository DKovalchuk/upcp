# SPEC-0015: M15 — Production Ready

**Version:** 1.0
**Date:** 2026-08-07
**Status:** Draft
**Milestone:** M15 (0.17.0)

## 1. Objective

Transform UPCP from development-ready to production-ready by completing the agent workflow (M9), evidence & review engine (M10), and remaining frontend features (M11).

## 2. Success Criteria

- [ ] Agent can claim a task, send heartbeats, and complete it
- [ ] Human can request/answer clarifications with agents
- [ ] Evidence can be attached and verified (agent + human)
- [ ] DoD coverage is calculated and displayed
- [ ] Review rounds can be created with findings and verdicts
- [ ] Notifications system works (in-app)
- [ ] Reports can be generated and viewed
- [ ] Graceful shutdown is implemented
- [ ] All new endpoints have tests
- [ ] Frontend components have unit tests
- [ ] E2e tests cover critical agent workflows
- [ ] Pipeline passes all jobs

## 3. Scope

### 3.1 In Scope (M15)

| Milestone | Components | Tasks |
|-----------|------------|-------|
| M9 | agent-workflow | 8 tasks |
| M10 | quality-evidence | 7 tasks |
| M11 | notifications, reporting-insights | 7 tasks |
| M8 | runtime-platform | 2 tasks |

**Total: 24 tasks, ~60 story points**

### 3.2 Out of Scope (Future)

- M11: Full email/webhook notification channels
- M11: PDF report generation
- M11: OpenTelemetry full tracing
- M11: Agent inbox real-time streaming

## 4. Sprint Plan

### Sprint 1: Agent Workflow Core (S17.1) — 2 weeks, ~15 points

**Focus:** Task claim, heartbeat, stale detection

| Item | Task | Points | Priority |
|------|------|--------|----------|
| 7.1 | Implement task claim endpoint | 5 | Critical |
| 7.2 | Implement heartbeat endpoint | 4 | Critical |
| 7.3 | Implement stale claim detection | 3 | High |
| 7.4 | Add auth to agent endpoints | 3 | Critical |

**Deliverables:**
- POST /tasks/{id}/claim
- POST /tasks/{id}/heartbeat
- Background job for stale detection
- Agent token auth middleware

**Tests:**
- Unit: TaskService.claim, TaskService.heartbeat
- Integration: claim/release/heartbeat flow
- E2e: agent claims task → heartbeat → completes

### Sprint 2: Clarification & Context (S17.2) — 2 weeks, ~12 points

**Focus:** Clarification flow, context packs

| Item | Task | Points | Priority |
|------|------|--------|----------|
| 7.5 | Implement clarification request | 4 | High |
| 7.6 | Implement clarification answer | 4 | High |
| 7.7 | Implement context pack generator | 4 | Medium |

**Deliverables:**
- POST /tasks/{id}/clarifications
- POST /clarifications/{id}/answer
- POST /clarifications/{id}/resolve
- GET /tasks/{id}/context-pack

**Tests:**
- Unit: ClarificationService, ContextPackService
- Integration: request → answer → resolve flow
- E2e: agent asks clarification → human answers → agent continues

### Sprint 3: Evidence & DoD (S17.3) — 2 weeks, ~14 points

**Focus:** Evidence attachment, verification, DoD coverage

| Item | Task | Points | Priority |
|------|------|--------|----------|
| 8.1 | Implement evidence attachment | 5 | Critical |
| 8.2 | Implement evidence verification | 4 | High |
| 8.3 | Implement DoD item management | 3 | High |
| 8.4 | Implement coverage calculation | 2 | Medium |

**Deliverables:**
- POST /tasks/{id}/evidence
- POST /evidence/{id}/agent-verify
- POST /evidence/{id}/human-accept
- POST /evidence/{id}/reject
- GET /tasks/{id}/dod-items
- GET /tasks/{id}/dod-coverage

**Tests:**
- Unit: EvidenceService, DoDService
- Integration: attach → verify → accept flow
- E2e: agent attaches evidence → human verifies → DoD updated

### Sprint 4: Review Rounds (S17.4) — 2 weeks, ~12 points

**Focus:** Review lifecycle, findings, verdicts

| Item | Task | Points | Priority |
|------|------|--------|----------|
| 8.5 | Implement review round creation | 5 | Critical |
| 8.6 | Implement review verdict | 4 | High |
| 8.7 | Implement acceptance criteria | 3 | Medium |

**Deliverables:**
- POST /tasks/{id}/review-rounds
- POST /review-rounds/{id}/start
- POST /review-rounds/{id}/findings
- POST /review-rounds/{id}/verdict
- Acceptance criteria CRUD

**Tests:**
- Unit: ReviewService
- Integration: create → start → findings → verdict flow
- E2e: task submitted for review → reviewer approves → task done

### Sprint 5: Notifications & Reports (S17.5) — 2 weeks, ~10 points

**Focus:** In-app notifications, reports, graceful shutdown

| Item | Task | Points | Priority |
|------|------|--------|----------|
| 9.1 | Implement in-app notifications | 3 | Medium |
| 9.2 | Implement report generation | 3 | Medium |
| 9.3 | Implement dashboard stats | 4 | High |
| 9.4 | Implement graceful shutdown | 2 | Low |

**Deliverables:**
- POST /notifications (create)
- GET /notifications (list with pagination)
- PUT /notifications/{id}/read
- GET /reports (list)
- POST /reports/generate
- GET /api/v1/dashboard/stats
- Signal handling, connection drain

**Tests:**
- Unit: NotificationService, ReportService
- Integration: notification creation → read flow
- E2e: dashboard stats displayed correctly

## 5. Technical Design

### 5.1 Agent Workflow State Machine

```
backlog → ready → claimed → in_progress → done
                │         │
                │         ├──→ blocked → in_progress
                │         │
                │         ├──→ needs_clarification → in_progress
                │         │
                │         └──→ ready_for_review → done
                │
                └──→ cancelled
```

### 5.2 Evidence Verification Flow

```
unverified → agent_verified → human_accepted
    │
    └──→ rejected
    │
    └──→ stale
```

### 5.3 Review Round Flow

```
pending → in_progress → completed (with verdict)
    │
    └──→ cancelled
```

### 5.4 API Endpoints

**Agent Workflow:**
- POST /tasks/{id}/claim
- POST /tasks/{id}/release
- POST /tasks/{id}/heartbeat
- POST /tasks/{id}/clarifications
- POST /clarifications/{id}/answer
- POST /clarifications/{id}/resolve
- GET /tasks/{id}/context-pack

**Evidence & DoD:**
- POST /tasks/{id}/evidence
- POST /evidence/{id}/agent-verify
- POST /evidence/{id}/human-accept
- POST /evidence/{id}/reject
- GET /tasks/{id}/dod-items
- GET /tasks/{id}/dod-coverage

**Review:**
- POST /tasks/{id}/review-rounds
- POST /review-rounds/{id}/start
- POST /review-rounds/{id}/findings
- POST /review-rounds/{id}/verdict

**Notifications:**
- GET /notifications
- PUT /notifications/{id}/read
- PUT /notifications/read-all

**Reports:**
- GET /reports
- POST /reports/generate
- GET /reports/{id}

### 5.5 Database Changes

New tables (already exist in schema):
- task_claim (id, task_id, agent_id, state, claimed_at, released_at, expires_at, last_heartbeat_at)
- heartbeat (claim_id, progress_percent, current_step, next_step, blockers, eta)
- clarification_request (id, task_id, author_type, author_id, question, blocking, state, answer)
- evidence (id, task_id, dod_item_id, type, title, url, content_snippet, verification_state)
- review_round (id, task_id, reviewer_type, reviewer_id, state, verdict, confidence, summary)
- review_finding (id, review_round_id, severity, category, message, evidence_id)
- notification (id, user_id, type, title, message, entity_type, entity_id, is_read)

### 5.6 Frontend Components

**New pages/components:**
- AgentInbox page (list of pending tasks/clarifications)
- EvidencePanel in TaskDetailSheet
- ReviewPanel in TaskDetailSheet
- NotificationBell dropdown
- ReportsPage enhancements

## 6. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent workflow complexity | High | Start with MVP, iterate |
| Evidence verification UX | Medium | Simple approve/reject flow first |
| Notification delivery | Low | In-app only in M15, email later |
| Review round edge cases | Medium | Limit to single reviewer initially |

## 7. Dependencies

- M7 (Identity & Access) — DONE
- M8 (Runtime Platform) — DONE (Redis, rate limiting)
- M9 (Agent Workflow) — Building on M7/M8
- M10 (Evidence & Review) — Building on M9
- M11 (Frontend) — Building on M7-M10

## 8. Definition of Done

- [ ] All acceptance criteria met
- [ ] Tests written and passing
- [ ] API documentation updated
- [ ] Frontend components tested
- [ ] E2e tests for critical flows
- [ ] Pipeline green
- [ ] Code reviewed
- [ ] Deployed to stage
