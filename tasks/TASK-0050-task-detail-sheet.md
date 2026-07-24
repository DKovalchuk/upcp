# TASK-0050: Task Detail Sheet (Slide-Over)

**Status**: pending
**Spec**: SPEC-0012 §4.6, SPEC-0013 §3
**Phase**: 1 (Core Pages)
**Depends on**: TASK-0043, TASK-0044
**Blocks**: TASK-0049, TASK-0051
**Estimated effort**: 4-5 hours

---

## Problem

No task detail view exists. Users cannot see task metadata, acceptance criteria, DoD items, or subtasks.

## Acceptance Criteria

- [ ] `TaskDetailSheet` uses shadcn `Sheet` (right side, w-[500px])
- [ ] Header: Task title + status badge + priority dot + close button
- [ ] Metadata section: Feature, Component, Module, Assignee, Created (relative), Updated (relative)
- [ ] Tab navigation: Details | Acceptance Criteria | DoD | Subtasks
- [ ] Details tab:
  - Description (editable textarea or read-only)
  - Status dropdown (inline update)
  - Priority selector (inline update)
- [ ] AC tab:
  - List of acceptance criteria with checkbox (toggle status)
  - "Add AC" input at bottom
  - Delete AC with trash icon
- [ ] DoD tab:
  - List of DoD items with checkbox (toggle status)
  - "Add DoD Item" input at bottom
  - Delete DoD item with trash icon
- [ ] Subtasks tab:
  - List of subtasks with status badge
  - "Add Subtask" input at bottom
  - Click subtask → inline edit
  - Delete subtask
- [ ] Delete task button in header → ConfirmDialog → close sheet + refresh list
- [ ] Toast on all mutations
- [ ] Sheet state managed by parent: `selectedTaskId: string | null`
- [ ] `npm run build` passes

## Technical Notes

- Use `useTask(id)` for task data
- Use `useAcceptanceCriteria(taskId)`, `useDoDItems(taskId)`, `useSubtasks(taskId)`
- Inline updates via `useUpdateAcceptanceCriterion()`, etc.
- Checkbox toggle: optimistic update, rollback on error
- Sheet component: `import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'`
