# TASK-0121: Task Distribution Donut Chart

**Spec:** SPEC-0025 S25.2
**Status:** DONE (closed 2026-10-16)
**Priority:** HIGH
**Effort:** 5pts

## Objective

Add a Recharts donut chart showing task distribution by status, with click-through to filtered views.

## Changes

### Frontend
- Install `recharts` if not present: `npm install recharts`
- Create `TaskDistributionDonut` component in `frontend/src/components/dashboard/`
- Data source: `task_counts_by_status` from `useDashboardStats()`
- Chart: Recharts `PieChart` with `innerRadius` for donut effect
- Colors: backlog=#94a3b8, in_progress=#3b82f6, review=#f59e0b, done=#10b981, blocked=#ef4444
- Center label: total task count
- Click sector → `navigate({ to: '/delivery', search: { status: sectorName } })`
- Legend below chart with counts
- Empty state: "No tasks yet" message
- Responsive: wrap in `ResponsiveContainer`

## Acceptance Criteria

- [ ] Donut chart renders with correct proportions
- [ ] Each sector is clickable → navigates to `/delivery?status=X`
- [ ] Center shows total count
- [ ] Legend shows status name + count
- [ ] Hover shows tooltip with percentage
- [ ] Empty state when no tasks
- [ ] Responsive on all screen sizes
- [ ] Dark mode colors work
