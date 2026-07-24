# TASK-0051: Quality Page

**Status**: pending
**Spec**: SPEC-0012 §4.7, SPEC-0013 §3
**Phase**: 2 (Extended)
**Depends on**: TASK-0046, TASK-0050
**Estimated effort**: 2-3 hours

---

## Problem

No Quality page exists. Backend has `GET /api/v1/projects/:id/quality/stats` returning aggregated quality data that is not consumed.

## Acceptance Criteria

- [ ] Quality tab in Project Detail renders `QualityPage`
- [ ] Stats row: 4 cards — Total Tasks, Tasks with AC, AC Pass Rate (%), DoD Pass Rate (%)
- [ ] Progress bars for AC and DoD completion
- [ ] Task quality table: Task title, AC count, DoD count, AC passed/total, DoD passed/total
- [ ] Click task → opens TaskDetailSheet (reuse from TASK-0050)
- [ ] Loading: skeleton
- [ ] Empty: "No tasks with quality criteria yet"
- [ ] `npm run build` passes

## Technical Notes

- Use `useQualityStats(projectId)` hook
- Backend returns: `total_tasks`, `tasks_with_ac`, `total_ac`, `passed_ac`, `total_dod`, `passed_dod`, `pass_rate`
- Progress bar: shadcn `Progress` component
- Pass rate: `(passed / total * 100).toFixed(1)`%
