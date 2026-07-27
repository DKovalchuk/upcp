# SPEC-0006 Project CRUD

Status: approved
Owner: project-owner
Milestone: M1
Related tasks: TASK-0006

## Problem

No project entity exists. UPCP is a project control plane — this is the core entity.

## Goal

Full CRUD for Project: create, read, update, delete, list.

## Non-goals

- No RBAC enforcement yet (TASK-0008).
- No audit events on every action yet (added when audit integration is wired).
- No components/modules yet (M2).

## Requirements

1. Project model: id, name, slug (unique), description, status, created_at, updated_at.
2. Create: POST /api/v1/projects — validates slug uniqueness.
3. Read: GET /api/v1/projects/{project_id}.
4. Update: PATCH /api/v1/projects/{project_id} — partial update.
5. Delete: DELETE /api/v1/projects/{project_id} — hard delete.
6. List: GET /api/v1/projects — paginated.
7. Slug auto-generated from name if not provided.
8. Status enum: active, paused, archived.

## Acceptance Criteria

- All CRUD endpoints work.
- Slug uniqueness enforced.
- Pagination on list.
- 404 on not found.
- Tests for all scenarios.
- Coverage >= 80%.
- Migration generated.

## DoD

- Spec approved.
- Task implemented with TDD.
- All commands pass.
- Statuses updated.
