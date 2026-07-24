# TASK-0049: Delivery Page (Features + Tasks)

**Status**: done
**Spec**: SPEC-0012 §4.5, SPEC-0013 §3
**Phase**: 1 (Core Pages)
**Depends on**: TASK-0046, TASK-0047, TASK-0050
**Estimated effort**: 4-5 hours

---

## Problem

No Delivery page exists. Users cannot view or manage features and tasks.

## Acceptance Criteria

- [ ] Delivery tab in Project Detail renders `DeliveryPage`
- [ ] Toolbar: SearchInput, status filter Select, + Feature button
- [ ] Features listed as expandable sections
- [ ] Each feature section: name + status badge + task count, edit/delete dropdown
- [ ] Feature expands to show task table
- [ ] Task table columns: Priority (dot), Title, Status (badge), Assignee, Component, Updated, Actions
- [ ] Task row click → opens TaskDetailSheet
- [ ] Create task button inside feature section
- [ ] Search filters tasks by title (client-side or debounced API call)
- [ ] Status filter: dropdown with all status values
- [ ] Create/edit/delete feature via FeatureForm dialog
- [ ] Create/edit/delete task via TaskForm dialog
- [ ] Toast on all mutations
- [ ] Loading: skeleton
- [ ] Empty: "No features yet" with create CTA
- [ ] `npm run build` passes

## Technical Notes

- Use `useFeatures(projectId)` for feature list
- Use `useTasks(featureId)` for each expanded feature
- Task list lazy-loaded on feature expand
- Search: debounce 300ms, filter client-side for small lists
