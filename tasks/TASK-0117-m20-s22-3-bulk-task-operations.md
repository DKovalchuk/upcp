# TASK-0117 — M20 S22.3: Bulk Task Operations

**Milestone:** M20
**Sprint:** S22.3
**Points:** 5
**Spec:** SPEC-0023 §S22.3
**Status:** DONE

## Objective

Select multiple tasks and perform batch actions: bulk status change, bulk assign, bulk priority change.

## Acceptance Criteria

- [ ] `PATCH /api/v1/tasks/bulk` accepts `{task_ids: [], updates: {}}` and returns `{updated: int}`
- [ ] Bulk status change validates lifecycle transitions per task
- [ ] Bulk assign sets `assignee_type` + `assignee_id` on all selected tasks
- [ ] Bulk priority change sets `priority` on all selected tasks
- [ ] Frontend: checkbox column in task table (select all/none)
- [ ] Frontend: bulk actions dropdown (Change Status, Assign, Change Priority)
- [ ] Frontend: confirmation dialog for status changes
- [ ] All existing task tests still pass
- [ ] New bulk tests: valid bulk update, empty list, invalid status, mixed results

## Technical Design

### Backend

**New endpoint:** `PATCH /api/v1/tasks/bulk`
- Body: `BulkTaskUpdate` schema with `task_ids: list[str]`, `updates: TaskBulkUpdates`
- `TaskBulkUpdates`: optional `status`, `priority`, `assignee_type`, `assignee_id`
- Returns `{updated: int}` count
- Each task validated independently; failures logged but don't block others

**New schema:** `BulkTaskUpdate`, `TaskBulkUpdates`

**Service method:** `TaskService.bulk_update(task_ids, **updates)` → int

### Frontend

- Checkbox column in TaskTable/BoardView
- Select all checkbox in header
- BulkActions toolbar appears when items selected
- Actions: Change Status (dropdown), Assign (input), Change Priority (dropdown)
- Confirmation dialog for status changes

## Files to Create/Modify

- `backend/app/delivery/schemas.py` — BulkTaskUpdate, TaskBulkUpdates
- `backend/app/delivery/service.py` — bulk_update method
- `backend/app/api/v1/delivery.py` — PATCH /tasks/bulk endpoint
- `backend/tests/test_bulk_tasks.py` — tests
- `frontend/src/lib/api/tasks.ts` — bulkUpdateTasks function
- `frontend/src/hooks/use-tasks.ts` — useBulkUpdateTasks hook
- `frontend/src/components/project/TaskTable.tsx` — checkbox column + bulk actions
