# TASK-0123: Clickable Attention Items

**Spec:** SPEC-0025 S25.4
**Status:** DONE (closed 2026-10-16)
**Priority:** HIGH
**Effort:** 3pts

## Objective

Make all attention items clickable with proper navigation. Add missing LowHealthProjects section.

## Changes

### Frontend — AttentionCards.tsx
- Wrap each attention item in `<Link>` or `<button onClick={navigate}>`
- Task items (review/blocked/failed/rejected/stale):
  - Navigate to `/projects/:projectId/delivery` and open TaskDetailSheet via URL param
  - Or use existing task detail route if available
- Clarification items → navigate to task detail → Clarifications tab
- Add "View all →" link when section has >3 items → navigates to filtered view
- Add new `LowHealthProjectsSection` card:
  - Shows projects with health_score <80
  - Each item: project name, health score (color-coded bar), top issue
  - Click → `/projects/:id`

### Frontend — types
- Update `AttentionItem` type to include `task_id`, `project_id`, `entity_url` fields
- Backend already returns these in most cases

## Acceptance Criteria

- [ ] Every attention item is clickable
- [ ] Task items open task detail
- [ ] Clarification items navigate to task clarifications
- [ ] Low health projects section renders with health scores
- [ ] "View all →" link appears when >3 items
- [ ] Cursor changes to pointer on hover
- [ ] Keyboard accessible (Enter/Space activates link)
