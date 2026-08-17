# TASK-0112 — M19 S21.1: Test Infrastructure

**Milestone:** M19
**Sprint:** S21.1
**Points:** 5
**Spec:** SPEC-0022 §S21.1
**Status:** PENDING

## Objective

Unify test infrastructure: centralize conftest, add pytest markers, add frontend coverage.

## Acceptance Criteria

- [ ] Engine duplication eliminated — all test files use shared engine from conftest.py
- [ ] conftest.py imports all models for `create_all()`
- [ ] Pytest markers added: `@pytest.mark.slow`, `@pytest.mark.integration`
- [ ] Frontend: `@vitest/coverage-v8` configured in vitest.config
- [ ] All existing tests still pass
- [ ] `pytest --markers` shows custom markers

## Technical Design

### Backend conftest unification

Move duplicated engine/session setup from 8+ test files into `tests/conftest.py`:

```python
# tests/conftest.py
from app.shared.database import engine, Base

@pytest.fixture(scope="session")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
```

Remove individual `create_engine` calls from test files.

### Pytest markers

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m not slow')",
    "integration: marks integration tests requiring full stack",
]
```

### Frontend coverage

Add to `frontend/vitest.config.ts`:

```ts
coverage: {
  provider: 'v8',
  reporter: ['text', 'lcov'],
  include: ['src/**/*.{ts,tsx}'],
}
```

Add `test:coverage` script to `frontend/package.json`.
