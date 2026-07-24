# SPEC-0008 Structure: Component + Module CRUD

Status: approved
Owner: project-owner
Milestone: M2
Related tasks: TASK-0009

## Problem

No structural hierarchy exists. Projects need components and modules for organization.

## Goal

Component and Module CRUD under a Project.

## Non-goals

- No delivery entities yet (M2-TASK-0010).
- No cross-project components.

## Requirements

1. Component: id, project_id (FK), name, slug (unique per project), description, status, timestamps.
2. Module: id, component_id (FK), name, slug (unique per component), description, status, timestamps.
3. CRUD endpoints: create, read, update, delete, list (with project/component scoping).
4. Slug uniqueness scoped to parent (project for component, component for module).

## Acceptance Criteria

- Full CRUD for components scoped to project.
- Full CRUD for modules scoped to component.
- Slug uniqueness within parent.
- 404 on missing parent.
- Tests for all scenarios.
- Coverage >= 80%.
- Migration generated.

## DoD

- Spec approved.
- Task implemented with TDD.
- All commands pass.
- Statuses updated.
