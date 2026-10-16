# TASK-0125: Project Selector + Dashboard Scoping

**Spec:** SPEC-0025 S25.6
**Status:** DONE (closed 2026-10-16)
**Priority:** MEDIUM
**Effort:** 3pts

## Objective

Add a project selector dropdown that scopes the entire dashboard to a selected project.

## Changes

### Frontend
- Create `ProjectSelector` component using shadcn `Select`
- Default: "All Projects"
- Options: from `useProjects()` hook
- Selection stored in URL search param: `?project_id=xxx`
- Use TanStack Router's `useNavigate` + `useSearch` for URL state
- Pass `projectId` to all dashboard hooks:
  - `useDashboardStats(projectId)`
  - `useAttentionDashboard(projectId)`
  - `useVelocity(projectId)`
  - `usePortfolioOverview()` (always global)
- When project selected: KPI cards show project-scoped data
- When "All Projects": show aggregate data

### Backend
- Update `/dashboard/stats` to accept optional `project_id` query param
- When provided: filter all counts to that project's tasks/features
- Update `/dashboard/attention` similarly
- Update `/analytics/velocity` to accept `project_id`

## Acceptance Criteria

- [ ] Dropdown shows all projects + "All Projects" option
- [ ] Selection updates URL param
- [ ] Dashboard data updates when selection changes
- [ ] URL with `?project_id=xxx` loads scoped dashboard
- [ ] "All Projects" shows aggregate data
- [ ] Dropdown styled consistently with app
