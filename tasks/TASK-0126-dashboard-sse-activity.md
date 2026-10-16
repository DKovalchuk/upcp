# TASK-0126: Activity Feed via SSE

**Spec:** SPEC-0025 S25.7
**Status:** DONE (closed 2026-10-16)
**Priority:** LOW
**Effort:** 3pts

## Objective

Replace 60s polling with SSE for real-time activity feed updates.

## Changes

### Frontend
- In `LiveActivityFeed.tsx`, add SSE subscription for activity events
- Reuse existing `useSSE` hook (already receives notifications)
- On SSE notification event → invalidate `dashboard-stats` query → activity feed updates
- Fallback: keep existing30s polling if SSE disconnected
- Add `isConnected` indicator (green dot when SSE active)
- Click event → navigate to entity detail (already partially implemented)

### Backend
- Ensure SSE stream emits events for task.claimed, task.status_changed, evidence.attached, review.completed
- These should already be emitted by the notification system

## Acceptance Criteria

- [ ] Activity feed updates within 2s of new event (via SSE)
- [ ] Green indicator when SSE connected
- [ ] Falls back to30s polling when SSE disconnects
- [ ] Click event navigates to entity detail
- [ ] No duplicate events in feed
- [ ] Max20 events shown, older ones scroll off
