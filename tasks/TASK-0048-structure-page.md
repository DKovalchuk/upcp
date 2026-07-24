# TASK-0048: Structure Page (Components + Modules)

**Status**: pending
**Spec**: SPEC-0012 §4.4, SPEC-0013 §3
**Phase**: 1 (Core Pages)
**Depends on**: TASK-0046, TASK-0047
**Estimated effort**: 3-4 hours

---

## Problem

No Structure page exists. Users cannot view or manage components and modules.

## Acceptance Criteria

- [ ] Structure tab in Project Detail renders `StructurePage`
- [ ] Components displayed as cards in a responsive grid
- [ ] Each component card shows: name, slug, status badge, description, module count
- [ ] Component card has dropdown menu: Edit, Delete
- [ ] Click component card → expands inline to show modules table
- [ ] Modules table columns: Name, Slug, Status, Actions (edit, delete)
- [ ] "Create Component" button opens ComponentForm dialog
- [ ] "Create Module" button inside expanded card opens ModuleForm dialog
- [ ] Delete component/module with ConfirmDialog
- [ ] Toast on all mutations
- [ ] Loading: skeleton cards
- [ ] Empty: "No components yet. Create your first component." with CTA
- [ ] `npm run build` passes

## Technical Notes

- Use `useComponents(projectId)` for component list
- Use `useModules(componentId)` for each expanded component
- Module list is lazy-loaded only when component is expanded
- Card grid: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`
