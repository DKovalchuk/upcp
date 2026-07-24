# TASK-0047: Create/Edit Form Dialogs (All Entities)

**Status**: done
**Spec**: SPEC-0013 §3
**Phase**: 1 (Core Pages)
**Depends on**: TASK-0044
**Blocks**: TASK-0048, TASK-0049
**Estimated effort**: 4-5 hours

---

## Problem

No create or edit forms exist for any entity. The "New Project" button is non-functional.

## Scope

Create form dialogs for: Project, Component, Module, Feature, Task, Subtask.

## Acceptance Criteria (per form)

- [ ] Uses shadcn `Dialog` component
- [ ] Fields match backend create/update schemas
- [ ] Required fields validated (name/title)
- [ ] Slug auto-generated from name (editable, kebab-case)
- [ ] Status field uses `Select` dropdown with valid values
- [ ] Priority field (Task only) uses Select with 0-3 options
- [ ] Parent selectors where needed (Component → project, Module → component, Feature → project+component, Task → feature+component+module)
- [ ] Submit calls correct mutation hook
- [ ] Loading state on submit button
- [ ] Toast on success/error
- [ ] Dialog closes on success
- [ ] Parent component refreshes via query invalidation
- [ ] Works for both create (no initial data) and edit (with initial data)
- [ ] `npm run build` passes

## Form Fields Reference

| Entity | Required | Optional |
|---|---|---|
| Project | name | slug, description, status |
| Component | name | slug, description, status |
| Module | name | slug, description, status |
| Feature | name | slug, description, status, component_id |
| Task | title | description, status, priority, assignee_type, assignee_id, component_id, module_id |
| Subtask | title | description, status |

## Technical Notes

- Pattern: `interface FormProps { open: boolean; onOpenChange: (v: boolean) => void; onSuccess?: () => void; initialData?: Entity }`
- Use `useForm` or local state (no form library needed for simple forms)
- Slug generation: `name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')`
