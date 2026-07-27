# TASK-0043: Fix Type Mismatches + Sidebar Navigation

**Status**: done
**Spec**: SPEC-0013 §3
**Phase**: 0 (Foundation)
**Blocks**: All other UI tasks
**Estimated effort**: 1-2 hours

---

## Problem

Frontend TypeScript types don't match backend API responses. Sidebar navigation has empty paths and wrong items.

## Context

API audit (SPEC-0012-audit-report.md) found:
- Task type missing `feature_id` field
- AuditEvent type has wrong field names (`user_id` vs `actor_id`, `details` vs `payload`)
- Feature type missing `project_id`
- Subtask type missing `task_id`
- Sidebar project nav items have empty `path` values
- Sidebar shows wrong nav items (Tasks, Features, Docs instead of Structure, Delivery, Quality, Audit, Settings)
- Priority constants use string keys (P0-P3) but backend returns integers (0-3)
- Missing API functions for dashboard stats and quality stats

## Acceptance Criteria

- [ ] `frontend/src/types/task.ts` has `feature_id: string`
- [ ] `frontend/src/types/feature.ts` has `project_id: string`
- [ ] `frontend/src/types/subtask.ts` has `task_id: string`
- [ ] `frontend/src/types/audit.ts` matches backend `AuditEventResponse` exactly
- [ ] `frontend/src/types/api.ts` has `DashboardStatsResponse`, `QualityStatsResponse`, `TaskCountsByStatus`
- [ ] `frontend/src/lib/constants.ts` has correct project nav items with paths
- [ ] Priority constants use integer keys (0, 1, 2, 3)
- [ ] `frontend/src/lib/api.ts` has `fetchDashboardStats()` and `fetchQualityStats(projectId)`
- [ ] `frontend/src/hooks/use-dashboard.ts` exists
- [ ] Sidebar links work for project sub-pages
- [ ] `npm run build` passes with no TypeScript errors

## Technical Notes

- Backend `AuditEventResponse` fields: `id`, `timestamp`, `event_type`, `entity_type`, `entity_id`, `actor_type`, `actor_id`, `payload`, `note`
- Backend `DashboardStatsResponse` fields: `project_count`, `task_counts_by_status`, `recent_projects`, `recent_activity`
- Backend `QualityStatsResponse` fields: `total_tasks`, `tasks_with_ac`, `total_ac`, `passed_ac`, `total_dod`, `passed_dod`, `pass_rate`
- Priority mapping: 0=Critical, 1=High, 2=Medium, 3=Low
