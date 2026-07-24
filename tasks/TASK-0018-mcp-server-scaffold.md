# TASK-0018 MCP Server Scaffold

Status: done
Owner: backend-developer
Milestone: M4
Depends on: SPEC-0005 (shared utils)
Related tasks: TASK-0019, TASK-0020

## Problem

No MCP server exists for AI agents to interact with UPCP. Agents need a way to query projects and tasks via MCP protocol.

## Goal

Create `backend/app/mcp/` context with MCP server scaffold using FastAPI. Implement basic MCP tools: project_list, project_get, task_list, task_get. Provide resource for context_pack.

## Requirements

1. Create `backend/app/mcp/` context with `__init__.py`, `server.py`, `tools.py`, `resources.py`, `schemas.py`.
2. MCP server using FastAPI with `/mcp` endpoint.
3. Implement MCP tools: `project_list`, `project_get`, `task_list`, `task_get`.
4. Each tool: name, description, input schema, handler.
5. Resource endpoint: `context_pack` generator.
6. Add tests for MCP server endpoints.
7. Update `main.py` to include MCP router.

## Acceptance Criteria

- `backend/app/mcp/` context created with all files.
- MCP server endpoint `/mcp` responds.
- Tools are callable via MCP protocol.
- Context pack resource returns markdown.
- Tests pass.
- Lint and typecheck pass.

## DoD

- All acceptance criteria satisfied.
- `make test`, `make lint`, `make typecheck` pass.
- Status updated.