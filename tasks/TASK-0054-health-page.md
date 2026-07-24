# TASK-0054: Health Page

**Status**: done
**Spec**: SPEC-0012 §4.10, SPEC-0013 §3
**Phase**: 2 (Extended)
**Depends on**: TASK-0044
**Estimated effort**: 1 hour

---

## Problem

No Health page exists. Backend has `GET /health` endpoint.

## Acceptance Criteria

- [ ] Route `/health` renders `HealthPage`
- [ ] Shows card for backend service: status, uptime indicator
- [ ] Auto-refreshes every 30 seconds (existing hook does this)
- [ ] Status indicator: green dot for "ok", red for error
- [ ] Response time measured client-side (time the fetch call)
- [ ] Loading: skeleton
- [ ] Error: shows error state with retry
- [ ] `npm run build` passes

## Technical Notes

- Use existing `useHealth()` hook (already has 30s polling)
- Simple page — one card with status info
- Future: add DB connectivity, MCP server status when endpoints exist
