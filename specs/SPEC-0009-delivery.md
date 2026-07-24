# SPEC-0009 Delivery: Feature, Task, Subtask CRUD

Status: approved
Owner: project-owner
Milestone: M2
Related tasks: TASK-0010

## Problem

No delivery hierarchy exists. Projects need features, tasks, and subtasks for work tracking.

## Goal

Feature, Task, Subtask CRUD under a Project.

## Non-goals

- No acceptance criteria yet (TASK-0011).
- No quality gates yet (TASK-0012).

## Requirements

1. Feature: id, project_id (FK), name, slug, description, status, component_id (optional FK), timestamps.
2. Task: id, feature_id (FK), title, description, status, priority, assignee_type, assignee_id, component_id, module_id, timestamps.
3. Subtask: id, task_id (FK), title, description, status, timestamps.
4. CRUD endpoints for all three.
5. Slug uniqueness for Feature scoped to project.

## Acceptance Criteria

- Full CRUD for features, tasks, subtasks.
- Proper FK relationships.
- Coverage >= 80%.
- Migration generated.

## DoD

- Spec approved.
- Task implemented with TDD.
- All commands pass.
- Statuses updated.
