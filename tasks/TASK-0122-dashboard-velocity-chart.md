# TASK-0122: Velocity Line Chart

**Spec:** SPEC-0025 S25.3
**Status:** DONE (closed 2026-10-16)
**Priority:** MEDIUM
**Effort:** 5pts

## Objective

Add an 8-week velocity chart showing tasks completed per week.

## Changes

### Backend
- Create endpoint `GET /api/v1/analytics/velocity?weeks=8&project_id=xxx`
- Query: count tasks with `status=done` grouped by ISO week (`date_trunc('week', updated_at)`)
- Return: `{ items: [{ week: "2026-W35", count: 5 }, ...] }`
- Register in analytics router

### Frontend
- Create API function `fetchVelocity(projectId?, weeks?)` in `lib/api/analytics.ts`
- Create hook `useVelocity(projectId?, weeks?)` in `hooks/use-analytics.ts`
- Create `VelocityChart` component using Recharts `LineChart`
- X-axis: week labels (W35, W36, ...)
- Y-axis: task count
- Gradient area fill below line
- Hover tooltip: "Week 35: 5 tasks"
- Click data point → `/delivery?status=done&week=W35`
- Empty state: "No completed tasks yet"

## Acceptance Criteria

- [ ] Chart shows 8 weeks of data
- [ ] Correct weekly task completion counts
- [ ] Hover tooltip with details
- [ ] Click navigates to filtered delivery view
- [ ] Empty state for projects with no completed tasks
- [ ] Scoped to selected project when project_id provided
- [ ] Responsive
