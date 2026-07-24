# TASK-0057: Board/Kanban View for Delivery

**Status**: done
**Spec**: SPEC-0013 §6
**Phase**: 4 (Polish)
**Depends on**: TASK-0049, TASK-0050
**Estimated effort**: 3-4 hours

## Goal

Add a Kanban board view to the Delivery page, allowing users to visualize tasks by status in columns and change task status by clicking.

## Problem

Currently the Delivery page only shows a list/table view of features and tasks. A board view provides a better visual overview of work distribution across statuses.

## Scope

1. Create `frontend/src/components/project/BoardView.tsx`
2. Add view toggle (List / Board) to DeliveryPage header
3. Board columns: Backlog, In Progress, Review, Done
4. Each task rendered as a card with: title, priority dot, feature name, assignee
5. Click task card → opens TaskDetailSheet (reuse existing)
6. Click status badge on card → cycle to next status (backlog → in-progress → review → done)
7. Empty columns show placeholder text
8. Tasks filtered by search input (same as list view)

## Acceptance Criteria

- [ ] View toggle switches between List and Board
- [ ] Board shows 4 columns: Backlog, In Progress, Review, Done
- [ ] Task cards show title, priority, feature name
- [ ] Click card opens TaskDetailSheet
- [ ] Click status badge changes task status
- [ ] Search filter works in board view
- [ ] Empty columns show "No tasks" placeholder
- [ ] `npm run build` passes
- [ ] Tests pass
