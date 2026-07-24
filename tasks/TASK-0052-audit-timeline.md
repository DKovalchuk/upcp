# TASK-0052: Audit Timeline Page

**Status**: pending
**Spec**: SPEC-0012 §4.8, SPEC-0013 §3
**Phase**: 2 (Extended)
**Depends on**: TASK-0046, TASK-0043
**Estimated effort**: 2-3 hours

---

## Problem

No Audit page exists. Backend has `GET /api/v1/projects/:id/audit-events` with filtering and pagination.

## Acceptance Criteria

- [ ] Audit tab in Project Detail renders `AuditPage`
- [ ] Filters bar: event_type Select, entity_type Select, date_from/date_to inputs
- [ ] Timeline: vertical layout with event nodes
- [ ] Each timeline item shows:
  - Timestamp (relative: "2 hours ago")
  - Event type badge (created → green, updated → blue, deleted → red)
  - Entity type + entity ID
  - Actor type + actor ID
  - Expandable payload (JSON viewer or key-value list)
- [ ] Pagination: "Load more" button (offset-based)
- [ ] Filters trigger new API call
- [ ] Loading: skeleton
- [ ] Empty: "No audit events found"
- [ ] `npm run build` passes

## Technical Notes

- Use `useAuditEvents({ project_id, event_type, entity_type, date_from, date_to })`
- Backend returns: `{ items: AuditEvent[], total, offset, limit }`
- Relative time: use `Intl.RelativeTimeFormat` or simple helper
- Date inputs: native `<input type="date">` or shadcn date picker
