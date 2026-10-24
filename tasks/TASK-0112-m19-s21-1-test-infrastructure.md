# TASK-0112 — M19 S21.1: Test Infrastructure

**Milestone:** M19
**Sprint:** S21.1
**Points:** 5
**Spec:** SPEC-0022 §S21.1
**Status:** PARTIAL

**Audit 2026-10-24 (evidence):** markers ✅ (`pyproject.toml:50-54` slow/
integration/unit), coverage ✅ (`@vitest/coverage-v8`, `test:coverage`,
каталог `frontend/coverage/` с cobertura), conftest импортирует все модели ✅
(`tests/conftest.py:15-23`), suites зелёные ✅ (CI 465-469).
**Gap:** AC «engine duplication eliminated — all test files use shared
engine» не выполняется в текущем дереве: 17/89 тест-файлов создают собственные
`create_engine` (15 из них без `db_session`). Часть — post-M19 добавки
(TASK-0128/0142/0143), часть — намеренные сценарии (например,
`test_agent_create_commit.py` — два engine). Требуется разбор dedup vs
зафиксированные исключения → вынесено в очередь (см. PROJECT_STATUS).

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
