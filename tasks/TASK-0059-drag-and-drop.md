# TASK-0059: Drag-and-Drop for Board View

**Status**: done
**Spec**: SPEC-0013 §6
**Phase**: 3 (Polish)
**Depends on**: TASK-0057
**Estimated effort**: 2-3 hours

---

## Problem

Board view requires clicking status badges to change task status. Users expect to drag cards between columns.

## Scope

1. Install `@dnd-kit/core` and `@dnd-kit/sortable`
2. Wrap BoardView in `DndContext` with `DragOverlay`
3. Make task cards draggable (`useDraggable`)
4. Make columns droppable (`useDroppable`)
5. On drop: update task status via `useUpdateTask`
6. Visual feedback: dragged card overlay, column highlight on drag-over

## Acceptance Criteria

- [ ] `@dnd-kit/core` installed
- [ ] Task cards are draggable
- [ ] Columns accept drops
- [ ] Dropping a card on a different column updates task status
- [ ] Drag overlay shows card being dragged
- [ ] Column highlights when dragging over it
- [ ] Click on card still opens TaskDetailSheet (no regression)
- [ ] `npm run build` passes
- [ ] Tests pass

## Technical Notes

- `@dnd-kit/core` for DndContext, useDraggable, useDroppable
- `@dnd-kit/sortable` not needed (no reordering within columns)
- DragOverlay renders a clone of the dragged card
- onDragEnd: extract taskId from active, newStatus from over, call updateTask
