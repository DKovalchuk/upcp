# SPEC-0002 Shared Foundation: Config, Logging, Errors

Status: approved
Owner: project-owner
Milestone: M0
Related tasks: TASK-0002

## Problem

No typed configuration, structured logging, or error taxonomy exist. Every future module needs these.

## Goal

Provide the shared context with:

- typed app config (pydantic-settings, reads `.env`);
- structured logging (JSON-capable, level from env);
- error taxonomy (typed exceptions, FastAPI error handler).

## Non-goals

- No pagination (M1).
- No custom ID types (M1).
- No time utilities beyond stdlib.

## Requirements

1. Config loads from env vars / `.env` with defaults.
2. Config is a singleton, accessible via `get_settings()`.
3. Logging is structured, level configurable, no print() in app code.
4. Error taxonomy covers: `not_found`, `validation_error`, `conflict`, `internal_error`.
5. Error handler returns JSON in problem-like format.
6. All existing tests still pass.

## Acceptance Criteria

- `Settings` class reads env vars and defaults.
- `get_settings()` returns cached singleton.
- Logging setup produces structured output.
- Custom exceptions exist: `NotFound`, `ValidationError`, `Conflict`, `InternalError`.
- FastAPI app registers error handler for these exceptions.
- `make test`, `make lint`, `make typecheck` pass.
- No new external dependencies required.

## Risks

- Minimal: these are foundational modules with clear contracts.

## DoD

- Spec approved.
- Task implemented with TDD.
- All commands pass.
- Statuses updated.
