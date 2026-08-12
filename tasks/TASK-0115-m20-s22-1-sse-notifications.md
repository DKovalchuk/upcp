# TASK-0115 — M20 S22.1: Real-Time Notifications via SSE

**Milestone:** M20
**Sprint:** S22.1
**Status:** IN PROGRESS
**Spec:** SPEC-0023
**Estimate:** 8pts

## Objective

Replace 30s polling with Server-Sent Events for critical notifications.

## Acceptance Criteria

- [ ] Backend: SSE endpoint `GET /api/v1/notifications/stream`
- [ ] Backend: Event emitter on notification creation
- [ ] Frontend: `EventSource` connection with fallback to polling
- [ ] Toast for critical events (blocking clarification, review submitted)
- [ ] All existing tests pass

## Implementation Plan

1. **Backend SSE endpoint** — async generator yielding events
2. **Event emitter** — hook into NotificationService.create() to push events
3. **Frontend EventSource** — hook/useSSE with automatic reconnection
4. **Critical event toasts** — toast on clarification/review events
