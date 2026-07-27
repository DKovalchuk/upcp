# TASK-0045: Dashboard Page

**Status**: done
**Spec**: SPEC-0012 §4.1, SPEC-0013 §3
**Phase**: 1 (Core Pages)
**Depends on**: TASK-0043, TASK-0044
**Estimated effort**: 2-3 hours

---

## Problem

`/` route currently renders `ProjectList` instead of a proper dashboard. Backend has `GET /api/v1/dashboard/stats` returning aggregated data that is not consumed.

## Acceptance Criteria

- [ ] `/` route renders `Dashboard` component
- [ ] `/projects` route renders `ProjectList` component
- [ ] Dashboard shows 4 stat cards: Total Projects, Tasks by Status (with breakdown), Recent Activity count, System Health
- [ ] Recent Projects section shows last 5 projects with name, status, updated_at
- [ ] Activity Feed shows last 10 audit events
- [ ] Click project name → navigates to `/projects/:id`
- [ ] Loading state uses skeleton
- [ ] Empty state: "No projects yet" with create CTA
- [ ] Error state: ErrorState with retry
- [ ] `npm run build` passes

## Technical Notes

- Use `useDashboardStats()` hook from TASK-0043
- Stats cards: `Card` + icon + number + label
- Recent projects: simple table or card list
- Activity feed: list of `AuditEventSummary` with relative timestamps
- Use `date-fns` or inline `Intl.RelativeTimeFormat` for relative times
