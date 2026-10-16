# TASK-0115 — M20 S22.1: Real-Time Notifications via SSE

**Milestone:** M20
**Sprint:** S22.1
**Status:** DONE (closed 2026-10-17 — AC verified against code)
**Spec:** SPEC-0023
**Estimate:** 8pts

## Objective

Replace 30s polling with Server-Sent Events for critical notifications.

## Acceptance Criteria

- [x] Backend: SSE endpoint `GET /api/v1/notifications/stream` — `app/api/v1/notifications.py:95` (StreamingResponse + keepalive every 15s)
- [x] Backend: Event emitter on notification creation — `app/shared/event_setup.py` forwards event-bus events → `sse_manager.broadcast()`
- [x] Frontend: SSE connection with fallback to polling — `hooks/use-sse.ts` (reconnect 3s→30s backoff, invalidates `notifications`/`dashboard-stats`/`attention-dashboard`); fallback polling `refetchInterval: 30000` in `NotificationBell.tsx`. *Deviation: fetch-based stream reader instead of native `EventSource` — required to send the Authorization header*
- [x] Toast for critical events (blocking clarification, review submitted) — `use-sse.ts` `showToast.info` when `data.critical`
- [x] All existing tests pass — `tests/test_sse.py` 6 passed; full suites: backend 912, frontend 336/336

## Implementation Plan

1. **Backend SSE endpoint** — async generator yielding events
2. **Event emitter** — hook into NotificationService.create() to push events
3. **Frontend EventSource** — hook/useSSE with automatic reconnection
4. **Critical event toasts** — toast on clarification/review events
