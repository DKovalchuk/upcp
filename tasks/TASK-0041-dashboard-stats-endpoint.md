# TASK-0041: Dashboard Statistics Endpoint

Spec: SPEC-0012 (C3)
Status: pending
Priority: 1
Model: routine
Milestone: M5

## Goal

Add `GET /api/v1/dashboard/stats` endpoint returning aggregated dashboard data. No single endpoint currently provides project counts, task counts by status, or recent activity.

## API contract

```text
GET /api/v1/dashboard/stats

Response 200:
{
  "project_count": int,
  "task_counts_by_status": {
    "backlog": int,
    "in_progress": int,
    "review": int,
    "done": int
  },
  "recent_projects": [Project] (last 5, sorted by updated_at desc),
  "recent_activity": [AuditEvent] (last 10, sorted by timestamp desc)
}
```

## TDD Steps

1. Add `get_dashboard_stats()` to a dashboard/reporting service.
2. Create API route.
3. Add Pydantic response schema `DashboardStatsResponse`.
4. Write tests for: empty database, populated database.
5. Verify `make test` passes.

## Acceptance Criteria

- Endpoint returns project count, task counts by status, recent projects, recent activity.
- Handles empty database (all zeros/empty arrays).
- `recent_projects` limited to 5.
- `recent_activity` limited to 10.
- Tests cover: empty, populated.
- `make test` passes.

## DoD

- endpoint implemented;
- service method added;
- tests pass;
- task file updated.
