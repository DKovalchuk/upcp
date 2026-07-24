# SPEC-0005 Shared Utilities: Pagination, IDs, Schemas

Status: approved
Owner: project-owner
Milestone: M1
Related tasks: TASK-0005

## Problem

No shared pagination, typed IDs, or response schemas exist. Every API endpoint will need these.

## Goal

Provide:

- Pagination params (FastAPI dependency) and paginated response schema.
- Typed entity ID (newtype over str).
- Response schemas for errors and health.

## Non-goals

- No sorting/filtering (M1+ per module).
- No cursor-based pagination (offset/limit sufficient for v1).

## Requirements

1. `PaginationParams` dependency: `offset`, `limit` with defaults.
2. `PaginatedResponse[T]` generic schema: `items`, `total`, `offset`, `limit`.
3. `EntityId` newtype for typed IDs.
4. `ErrorResponse` schema: `error`, `detail`.
5. `HealthResponse` schema: `status`, `service`.
6. All existing tests still pass.

## Acceptance Criteria

- `shared/pagination.py` with `PaginationParams`, `PaginatedResponse`.
- `shared/schemas.py` with `ErrorResponse`, `HealthResponse`.
- `shared/ids.py` with `EntityId`.
- Tests for pagination bounds, schema validation.
- `make test`, `make lint`, `make typecheck` pass.
- Statuses updated.

## Risks

- Minimal: these are utility modules with clear contracts.

## DoD

- Spec approved.
- Task implemented with TDD.
- All commands pass.
- Statuses updated.
