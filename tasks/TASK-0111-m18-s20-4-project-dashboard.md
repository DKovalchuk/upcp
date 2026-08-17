# TASK-0111 — M18 S20.4: Project Dashboard Enhancement

**Milestone:** M18
**Sprint:** S20.4
**Points:** 5
**Status:** IN PROGRESS
**Spec:** SPEC-0021, §S20.4

## Objective

Enhance the project detail page with health score, task distribution chart, velocity sparkline, and recent activity.

## Acceptance Criteria

1. Health score card showing project health with score and trend indicator
2. Task completion donut chart (done/in-progress/backlog distribution)
3. Velocity sparkline (tasks completed per week, last 8 weeks)
4. Recent activity section (last 10 audit events for this project)
5. All existing tests pass + 8 new dashboard tests
6. TypeScript clean, pre-commit hooks pass

## Design Decisions

- Use recharts for donut chart and sparkline (add as dependency)
- Health score uses the existing fetchProjectHealth API
- Velocity data derived from task completion timestamps (client-side aggregation)
- Recent activity uses the existing audit API
- Charts follow the project's 6-color palette
- No emoji policy — use SVG icons for indicators

## Files to Create/Modify

### Frontend
- `frontend/src/components/project/ProjectOverview.tsx` — new overview tab with all 4 cards
- `frontend/src/components/project/HealthScoreCard.tsx` — new
- `frontend/src/components/project/TaskDistributionChart.tsx` — new donut chart
- `frontend/src/components/project/VelocitySparkline.tsx` — new sparkline
- `frontend/src/components/project/RecentActivity.tsx` — new activity feed
- `frontend/src/hooks/use-dashboard.ts` — add project-specific queries if needed
- `frontend/src/lib/api/dashboard.ts` — add fetchProjectActivity if needed

### Tests
- `frontend/src/components/project/__tests__/ProjectOverview.test.tsx` — new
