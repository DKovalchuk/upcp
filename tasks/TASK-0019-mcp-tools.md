# TASK-0019 MCP Tools: Project, Task, Feature

Status: done
Owner: backend-developer
Milestone: M4
Depends on: TASK-0018
Related tasks: TASK-0020

## Problem

MCP server scaffold exists but needs full tool implementations for project, task, and feature operations.

## Goal

Implement MCP tools for project, task, and feature CRUD operations. Each tool: name, description, input schema, handler.

## Requirements

1. Project tools: `project_create`, `project_update`, `project_delete`, `project_list`, `project_get`.
2. Task tools: `task_create`, `task_update`, `task_delete`, `task_list`, `task_get`.
3. Feature tools: `feature_create`, `feature_update`, `feature_delete`, `feature_list`, `feature_get`.
4. Each tool: name, description, input schema, handler.
5. Handlers call existing services (project, delivery).
6. Input validation using Pydantic schemas.
7. Error handling with MCP error responses.

## Acceptance Criteria

- All project tools implemented.
- All task tools implemented.
- All feature tools implemented.
- Tools are callable via MCP protocol.
- Tests for each tool.
- Lint and typecheck pass.

## DoD

- All acceptance criteria satisfied.
- `make test`, `make lint`, `make typecheck` pass.
- Status updated.