# TASK-0046: Project Detail Page (Tabbed Layout)

**Status**: pending
**Spec**: SPEC-0012 §4.3, SPEC-0013 §3
**Phase**: 1 (Core Pages)
**Depends on**: TASK-0043, TASK-0044
**Blocks**: TASK-0048, TASK-0049, TASK-0051, TASK-0052
**Estimated effort**: 3-4 hours

---

## Problem

`/projects/:id` has no route or component. Users cannot view project details or navigate to project sub-pages.

## Acceptance Criteria

- [ ] Route `/projects/$projectId` renders `ProjectDetail`
- [ ] Page header shows project name + status badge + description
- [ ] Tab navigation with tabs: Overview, Structure, Delivery, Quality, Audit, Settings
- [ ] Tab state synced with URL search param `?tab=`
- [ ] Overview tab shows:
  - Project info card (name, slug, description, status, created, updated)
  - Quick stats: component count, feature count, task status breakdown
  - Recent activity (last 5 audit events)
- [ ] Edit project via Dialog (ProjectForm)
- [ ] Delete project with ConfirmDialog → navigates to `/projects`
- [ ] BreadcrumbBar shows: Home > Projects > {project.name}
- [ ] Loading: skeleton
- [ ] Error: 404 if project not found
- [ ] `npm run build` passes

## Technical Notes

- Use TanStack Router `$projectId` param
- Use shadcn `Tabs` component
- Tab content rendered lazily (only active tab)
- BreadcrumbBar needs to resolve project name from route context
