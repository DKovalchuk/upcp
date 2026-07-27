# Testing Standards

## Coverage requirement

**Minimum code coverage: 80%** (`--cov-fail-under=0.8`).

Enforced via `pytest-cov` in `pyproject.toml` and `make coverage`.

## Test types

### 1. Unit tests

Test individual functions, classes, and methods in isolation.

- No real network calls.
- No real database.
- Use in-memory SQLite or mocks.
- Fast feedback (< 1s per test).

```text
backend/tests/test_*.py (default)
```

Covers:
- service logic;
- validators;
- schemas;
- utilities;
- error handlers;
- business rules.

### 2. Integration tests

Test multiple components working together.

- Real database (test DB or in-memory).
- Real HTTP requests (TestClient).
- Verify contracts between modules.

```text
backend/tests/integration/
```

Covers:
- API endpoints + DB;
- Alembic migrations;
- cross-module interactions;
- audit trail end-to-end.

### 3. Acceptance tests

Verify user-visible behavior from DoD and acceptance criteria.

```text
backend/tests/acceptance/
```

Covers:
- full CRUD flows;
- error scenarios;
- edge cases from specs;
- DoD validation.

### 4. End-to-end (E2E) tests

Full stack: API + DB + UI (when available).

```text
backend/tests/e2e/
```

Covers:
- user journeys;
- multi-step workflows;
- real browser interactions (Playwright).

### 5. UI tests (Playwright MCP)

When React frontend exists:

```text
frontend/tests/
```

Covers:
- component rendering;
- user interactions;
- responsive layouts;
- accessibility (WCAG 2.1 AA);
- visual regression.

## Test naming

```text
test_<behavior>_<condition>_<expected>
```

Examples:

```python
test_create_project_with_valid_data_returns_201
test_create_project_with_duplicate_slug_returns_409
test_list_projects_empty_offset_returns_empty_list
test_health_returns_ok
```

## Test structure (AAA)

```python
def test_example() -> None:
    # arrange
    ...

    # act
    ...

    # assert
    ...
```

## Test categories by scenario

### Positive scenarios

- Happy path with valid input.
- Default values.
- Optional fields omitted.
- Single item CRUD.
- Bulk operations.

### Negative scenarios

- Invalid input → 422.
- Not found → 404.
- Conflict → 409.
- Permission denied → 403.
- Empty body → 422.
- Missing required fields.

### Edge cases

- Boundary values (offset=0, limit=1, limit=100).
- Maximum length strings.
- Empty strings vs null.
- Unicode content.
- Concurrent operations.
- Large payloads.

## Test pyramid

```text
unit tests          70%
integration tests   20%
e2e/acceptance      10%
```

## Commands

```bash
make test          # run all tests
make coverage      # run with coverage report (fail if < 80%)
make lint          # lint check
make typecheck     # type check
```

## Rules

- TDD is mandatory for behavior-changing code.
- Bugfix requires regression test.
- Every task must include tests before implementation.
- Tests must be deterministic.
- No real secrets in tests.
- Use fixtures for repeated setup.
- Truncate long outputs in logs.
- Prefer fast feedback.
- Coverage threshold is enforced in CI.

## File organization

```text
backend/tests/
├── test_health.py          # unit
├── test_config.py          # unit
├── test_errors.py          # unit
├── test_database.py        # unit/integration
├── test_audit.py           # unit
├── test_pagination.py      # unit
├── test_schemas.py         # unit
├── integration/            # integration tests (future)
├── acceptance/             # acceptance tests (future)
└── e2e/                    # end-to-end tests (future)
```
