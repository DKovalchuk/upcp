# TASK-0021 Typer CLI

Status: done
Owner: backend-developer
Milestone: M4
Depends on: TASK-0019
Related tasks: TASK-0020

## Problem

No CLI exists for interacting with UPCP from terminal. Users need command-line interface.

## Goal

Create Typer CLI with commands: project list, project get, task list, task get, status.

## Requirements

1. Create `backend/cli.py` with Typer app.
2. Commands: `project list`, `project get`, `task list`, `task get`, `status`.
3. Each command: name, description, options, handler.
4. Handlers call existing services (project, delivery).
5. Output: formatted text or JSON.
6. Add tests for CLI commands.
7. Update `pyproject.toml` with CLI entry point.

## Acceptance Criteria

- `backend/cli.py` created with Typer app.
- All commands implemented.
- Commands work from terminal.
- Tests for each command.
- Lint and typecheck pass.

## DoD

- All acceptance criteria satisfied.
- `make test`, `make lint`, `make typecheck` pass.
- Status updated.