# TASK-0005 Shared Pagination, IDs, Schemas

Spec: SPEC-0005
Status: done
Priority: 10
Model: routine
Milestone: M1

## Goal

Add shared pagination, typed IDs, and response schemas.

## Non-goals

- No sorting/filtering.
- No cursor pagination.

## Files likely involved

```text
backend/app/shared/pagination.py
backend/app/shared/schemas.py
backend/app/shared/ids.py
backend/tests/test_pagination.py
backend/tests/test_schemas.py
```

## TDD Steps

1. Create failing tests.
2. Run tests, confirm failure.
3. Implement modules.
4. Run tests, confirm pass.
5. Run lint and typecheck.

## Acceptance Criteria

- `PaginationParams` with offset/limit.
- `PaginatedResponse` generic schema.
- `EntityId` newtype.
- `ErrorResponse`, `HealthResponse` schemas.
- `make test`, `make lint`, `make typecheck` pass.
- Statuses updated.

## DoD

- tests added;
- implementation added;
- commands pass;
- statuses updated.
