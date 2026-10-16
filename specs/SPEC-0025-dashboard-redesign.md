# SPEC-0025 — Dashboard Redesign

**Milestone:** M21
**Status:** APPROVED
**Created:** 2026-09-05
**Source:** UX audit + best practices research (Linear, GitHub Projects, Jira, Shortcut)

## 1. Problem

Current dashboard has critical UX gaps:
- KPI cards are display-only, no drill-down
- Attention items are not clickable (task_id available but no `<Link>`)
- `low_health_projects` data fetched but silently discarded
- `portfolio/overview` API exists but unused
- No charts, trends, or velocity data
- Activity feed polling 60s (too slow)
- No project selector or date range filter

## 2. Goals

1. Every number is clickable → drill-down to filtered view
2. Progressive disclosure: KPI → attention → trends → context
3. Use all existing API endpoints (low_health_projects, portfolio)
4. Add charts (Recharts): donut for status, line for velocity
5. Activity feed via SSE (existing `useSSE` hook)
6. Project-scoped dashboard via selector

## 3. Scope

### S25.1: KPI Cards with Drill-Down (TASK-0120, 5pts)

Replace 4 static stat cards with 5 clickable KPI cards.

| Card | Value | Click Target |
|------|-------|-------------|
| Projects | `project_count` | `/projects` |
| Active Tasks | `in_progress + claimed + blocked` | `/delivery?status=in_progress,claimed,blocked` |
| Done This Week | new field `done_this_week` | `/delivery?status=done&since=7d` |
| Blocked Tasks | `blocked` count | `/delivery?status=blocked` |
| Health Score | `health_score` (0-100) | `/projects/:id` (selected project) |

- Backend: add `done_this_week`, `blocked`, `claimed` to `/dashboard/stats`
- Backend: add `health_score` to stats (aggregate or per selected project)
- Frontend: `StatCard` wraps in `<Link>`, adds hover effect + "View →" hint
- Variant colors: primary, info, success, warning, danger

### S25.2: Task Distribution Donut (TASK-0121, 5pts)

Recharts `PieChart` showing task counts by status.

- Data: `task_counts_by_status` (backlog/in_progress/review/done/blocked)
- Colors: slate (backlog), blue (in_progress), amber (review), emerald (done), red (blocked)
- Click sector → `/delivery?status=X`
- Center label: total task count
- Responsive: `ResponsiveContainer`
- Empty state: "No tasks yet" message

### S25.3: Velocity Line Chart (TASK-0122, 5pts)

8-week velocity chart showing tasks completed per week.

- Backend: new endpoint `GET /api/v1/analytics/velocity?weeks=8`
- Returns: `[{week: "2026-W35", count: 5}, ...]`
- Frontend: Recharts `LineChart` with gradient area fill
- X-axis: week labels (W35, W36, ...)
- Y-axis: task count
- Hover tooltip: week + count
- Click data point → `/delivery?status=done&week=W35`

### S25.4: Clickable Attention Items (TASK-0123, 3pts)

Make all attention items navigable.

- Each item wraps in `<Link>` or `<button onClick={navigate}>`
- Task items (review/blocked/failed/rejected/stale) → open TaskDetailSheet
- Clarification items → `/delivery` + open task detail → Clarifications tab
- Low health projects → `/projects/:id`
- Add "View all →" link when >3 items per section
- Add `LowHealthProjectsSection` card (currently missing)

### S25.5: Portfolio Table (TASK-0124, 3pts)

Table of all projects with health scores (when >1 project).

- Data: `GET /api/v1/portfolio/overview` (endpoint exists, unused)
- Columns: Project Name, Health Score (color-coded bar), Tasks (done/total), Status, Top Issue
- Health colors: ≥80 green, 50-79 amber, <50 red
- Click row → `/projects/:id`
- "Show more" if >5 projects

### S25.6: Project Selector + Dashboard Scoping (TASK-0125, 3pts)

Dropdown to filter dashboard by project.

- Default: "All Projects" (global view)
- Options: list of projects from `/api/v1/projects`
- Selected project scopes: KPI cards, attention, velocity chart
- URL param: `?project_id=xxx` (shareable, bookmarkable)
- Persists selection in URL, not localStorage

### S25.7: Activity Feed via SSE (TASK-0126, 3pts)

Replace60s polling with SSE stream.

- Reuse existing `useSSE` hook + `/notifications/stream`
- Activity items update in real-time
- Fallback: keep30s polling if SSE disconnected
- Click event → navigate to entity detail

### S25.8: Responsive Layout Polish (TASK-0127, 2pts)

Final layout assembly and responsive design.

- Row1: 5 KPI cards (5-col desktop, 2-col tablet, 1-col mobile)
- Row2: Donut (1/3) + Velocity (2/3)
- Row3: Attention grid (3-col desktop, 2-col tablet, 1-col mobile)
- Row4: Activity feed (2/3) + Agent summary (1/3)
- Row5: Portfolio table (full width)
- Animations: stagger-fade-in on load
- Dark mode: all new components support `dark:` variants

## 4. API Changes

### Modified Endpoints

`GET /api/v1/dashboard/stats` — add fields:
```json
{
  "done_this_week": 12,
  "blocked_count": 1,
  "claimed_count": 2,
  "health_score": 92
}
```

### New Endpoints

`GET /api/v1/analytics/velocity?weeks=8&project_id=xxx`
```json
{
  "items": [
    {"week": "2026-W35", "count": 5},
    {"week": "2026-W36", "count": 8}
  ]
}
```

### Existing Endpoints (already available, need frontend integration)

- `GET /api/v1/dashboard/attention` — `low_health_projects` field
- `GET /api/v1/portfolio/overview` — full portfolio data
- `GET /api/v1/projects/{id}/health` — per-project health

## 5. Tech Stack

- **Charts:** Recharts (PieChart, LineChart, ResponsiveContainer)
- **Routing:** TanStack Router with URL search params
- **Data:** React Query with staleTime + refetchInterval
- **Components:** shadcn/ui (Card, Badge, Progress, Tooltip, Skeleton)
- **SSE:** existing `useSSE` hook (fixed in commit 9aa3ea7)

## 6. Out of Scope

- Custom dashboard layouts (drag-drop widgets)
- Dashboard settings/preferences persistence
- Export dashboard as PDF/image
- Real-time collaboration cursors
