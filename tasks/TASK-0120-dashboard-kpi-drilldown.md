# TASK-0120: Dashboard KPI Cards with Drill-Down

**Spec:** SPEC-0025 S25.1
**Status:** DONE (closed 2026-10-16)
**Priority:** HIGH
**Effort:** 5pts

## Objective

Replace 4 static stat cards with 5 clickable KPI cards that navigate to filtered views.

## Changes

### Backend
- Modify `DashboardService.get_stats()` to return: `done_this_week`, `blocked_count`, `claimed_count`, `health_score`
- `done_this_week`: count tasks with `status=done` and `updated_at >= now() - 7 days`
- `blocked_count`: count tasks with `status=blocked`
- `claimed_count`: count tasks with status `claimed` or active claims
- `health_score`: use `AttentionDashboardService.get_project_health()` when project_id provided, else aggregate

### Frontend
- Update `DashboardStatsResponse` type
- Redesign `StatCard` component: wrap in `<Link>`, add hover effect, "View →" hint
- Update Dashboard.tsx to render5 cards with correct drill-down targets:
  - Projects → `/projects`
  - Active Tasks → `/delivery?status=in_progress,claimed,blocked`
  - Done This Week → `/delivery?status=done&since=7d`
  - Blocked → `/delivery?status=blocked`
  - Health → `/projects/:id` (if project selected)

## Acceptance Criteria

- [ ] Each KPI card is clickable and navigates to correct filtered view
- [ ] Hover shows pointer cursor + "View →" hint
- [ ] `done_this_week` shows only tasks completed in last7 days
- [ ] Health score shows project-specific score when project selected
- [ ] Cards responsive: 5-col desktop, 2-col tablet, 1-col mobile
- [ ] Dark mode supported
