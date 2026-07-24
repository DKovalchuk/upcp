# TASK-0040: Quality Statistics Aggregation Endpoint

Spec: SPEC-0012 (C2)
Status: done
Priority: 1
Model: routine
Milestone: M5

## Goal

Add `GET /api/v1/projects/{project_id}/quality/stats` endpoint returning project-level quality statistics. Currently only per-task AC/DoD endpoints exist.

## API contract

```text
GET /api/v1/projects/{project_id}/quality/stats

Response 200:
{
  "total_tasks": int,
  "tasks_with_ac": int,
  "total_ac": int,
  "passed_ac": int,
  "total_dod": int,
  "passed_dod": int,
  "pass_rate": float  // 0-100
}
```

## TDD Steps

1. Add `get_quality_stats()` to delivery/quality service.
2. Create API route.
3. Add Pydantic response schema `QualityStatsResponse`.
4. Write tests for: empty project, project with tasks, project with AC/DoD.
5. Verify `make test` passes.

## Acceptance Criteria

- Endpoint returns aggregated stats for a project.
- `pass_rate` = (passed_ac + passed_dod) / (total_ac + total_dod) * 100.
- Handles empty project (all zeros).
- Tests cover: empty, partial, full data.
- `make test` passes.

## DoD

- endpoint implemented;
- service method added;
- tests pass;
- task file updated.
