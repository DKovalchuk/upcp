# TASK-0002 Config, Logging, Error Foundation

Spec: SPEC-0002
Status: done
Priority: 10
Model: routine
Milestone: M0

## Goal

Implement the shared context with config, logging, and error taxonomy.

## Non-goals

- No pagination.
- No custom IDs.
- No auth.

## Files likely involved

```text
backend/app/shared/config.py
backend/app/shared/logging.py
backend/app/shared/errors.py
backend/app/shared/__init__.py
backend/app/main.py
backend/tests/test_config.py
backend/tests/test_errors.py
```

## TDD Steps

1. Create failing tests for config, errors.
2. Run tests, confirm failure.
3. Implement minimal code.
4. Run tests, confirm pass.
5. Run lint and typecheck.

## Acceptance Criteria

- `Settings` reads env vars with defaults.
- `get_settings()` is a cached singleton.
- Custom exceptions: `NotFound`, `ValidationError`, `Conflict`, `InternalError`.
- Error handler returns JSON problem-like responses.
- `make test` passes.
- `make lint` passes.
- `make typecheck` passes.
- Task and PROJECT_STATUS updated.

## DoD

- tests added;
- implementation added;
- commands pass;
- statuses updated.
