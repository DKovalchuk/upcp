# Test Plan — UPCP v2

> Проект: UPCP | Статус: Draft | Обновлено: 2026-07-27

## 1. Обзор

Тестирование UPCP v2 следует пирамиде тестирования: много unit тестов, меньше integration, минимум E2E.

```
        ╱╲
       ╱E2E╲         ← 5-10 критических flows
      ╱──────╲
     ╱ Integr.╲      ← API + DB, MCP contract
    ╱──────────╲
   ╱   Unit     ╲    ← Backend: pytest, Frontend: vitest
  ╱──────────────╲
```

## 2. Unit Tests

### 2.1 Backend (pytest)

**Расположение:** `tests/unit/`
**Конфигурация:** `pyproject.toml [tool.pytest]`
**Запуск:** `make test-unit` или `pytest tests/unit/ -v`

| Модуль | Что тестируется | Цель |
|--------|----------------|------|
| `auth/` | JWT creation, validation, password hashing | 100% branches |
| `models/` | ORM mapping, constraints, defaults | все поля |
| `schemas/` | Pydantic validation, edge cases | 100% validators |
| `services/` | Business logic, state transitions | 100% happy + error paths |
| `rate_limit/` | Sliding window, whitelist | все лимиты |
| `evidence/` | Hash computation, completeness calc | 100% |
| `review/` | Round management, finding creation | 100% |

**Пример:**
```python
# tests/unit/services/test_task_service.py
class TestTaskClaim:
    async def test_claim_open_task(self, task_factory, agent):
        task = await task_factory(status="open")
        result = await TaskService.claim(task.id, agent.id)
        assert result.status == "claimed"
        assert result.agent_id == agent.id

    async def test_claim_already_claimed_raises(self, task_factory, agent):
        task = await task_factory(status="claimed", agent_id="other")
        with pytest.raises(TaskAlreadyClaimedError):
            await TaskService.claim(task.id, agent.id)

    async def test_claim_non_agent_role_raises(self, task_factory, user):
        task = await task_factory(status="open")
        with pytest.raises(PermissionDeniedError):
            await TaskService.claim(task.id, user.id)
```

### 2.2 Frontend (vitest)

**Расположение:** `frontend/src/__tests__/`
**Конфигурация:** `frontend/vitest.config.ts`
**Запуск:** `cd frontend && npm test`

| Модуль | Что тестируется | Цель |
|--------|----------------|------|
| `components/` | Rendering, interactions, props | 100% |
| `hooks/` | Custom hooks, state logic | 100% |
| `store/` | State management, actions | 100% |
| `utils/` | Pure functions, formatters | 100% |
| `api/` | API client, error handling | mock responses |

### 2.3 Coverage targets

| Компонент | Target | Minimum |
|-----------|--------|---------|
| Backend services | 90% | 80% |
| Backend schemas | 100% | 90% |
| Frontend components | 80% | 60% |
| Frontend hooks | 90% | 80% |

## 3. Integration Tests

### 3.1 API Integration

**Расположение:** `tests/integration/`
**Среда:** Test PostgreSQL (docker-compose.test.yml)
**Запуск:** `make test-integration`

**Что тестируется:**
- CRUD операции через HTTP → DB
- Auth flow: register → login → access → refresh
- RBAC: проверка permissions для каждой роли
- Rate limiting: получение 429 при превышении
- Error handling: корректные HTTP status codes

**Пример:**
```python
# tests/integration/test_tasks_api.py
class TestTasksAPI:
    async def test_create_task(self, client, auth_headers, project):
        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            json={"title": "Test task", "description": "Do something"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test task"
        assert data["status"] == "open"

    async def test_create_task_unauthorized(self, client):
        response = await client.post(
            "/api/v1/projects/xxx/tasks",
            json={"title": "Test"}
        )
        assert response.status_code == 401
```

### 3.2 Database Integration

**Что тестируется:**
- Миграции: up + down + up
- Foreign key constraints
- Unique constraints
- Indexes
- Cascade deletes

```python
# tests/integration/test_migrations.py
class TestMigrations:
    async def test_migrate_up(self):
        await alembic.upgrade("head")
        # Проверить, что все таблицы созданы

    async def test_migrate_down_and_up(self):
        await alembic.upgrade("head")
        await alembic.downgrade("-1")
        await alembic.upgrade("head")
        # Данные не потеряны, schema корректна
```

## 4. E2E Tests

**Расположение:** `tests/e2e/`
**Инструмент:** Playwright (frontend) + httpx (backend)
**Запуск:** `make test-e2e`

### 4.1 Критические flows

| # | Flow | Описание |
|---|------|----------|
| 1 | First run | Setup → project → task → claim → evidence → review → done |
| 2 | Agent auth | API key → claim → heartbeat → clarification → resolve |
| 3 | Attention dashboard | Open → see blocked → drill-down → answer → verify |

### 4.2 Smoke tests

```bash
# Минимальный smoke test после deploy
make smoke-test
# Проверяет: health, auth, CRUD
```

## 5. MCP Contract Tests

См. [mcp-contract-tests.md](./mcp-contract-tests.md) для деталей.

**Расположение:** `tests/mcp/`
**Запуск:** `make test-mcp`

## 6. Permission Matrix Tests

См. [permission-matrix-tests.md](./permission-matrix-tests.md) для деталей.

**Расположение:** `tests/permissions/`
**Запуск:** `make test-permissions`

## 7. Test Infrastructure

### 7.1 Fixtures

```python
# conftest.py
@pytest.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    app = create_app(override_session=db_session)
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
```

### 7.2 Factories

```python
# tests/factories.py
class TaskFactory:
    @classmethod
    async def create(cls, session, **kwargs):
        task = Task(
            title=kwargs.get("title", "Test task"),
            status=kwargs.get("status", "open"),
            project_id=kwargs.get("project_id"),
            **kwargs
        )
        session.add(task)
        await session.commit()
        return task
```

### 7.3 Docker Compose для тестов

```yaml
# docker-compose.test.yml
services:
  db-test:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: upcp_test
      POSTGRES_USER: upcp_test
      POSTGRES_PASSWORD: test
    tmpfs:
      - /var/lib/postgresql/data  # RAM disk для скорости
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U upcp_test"]
      interval: 2s
      timeout: 2s
      retries: 5
```

## 8. CI/CD Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - build

test:unit:
  stage: test
  script:
    - make test-unit
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'

test:integration:
  stage: test
  services:
    - postgres:16-alpine
    - redis:7-alpine
  script:
    - make test-integration

test:mcp:
  stage: test
  script:
    - make test-mcp

test:e2e:
  stage: test
  script:
    - make test-e2e
  artifacts:
    paths:
      - tests/e2e/screenshots/
```

## 9. Coverage Enforcement

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=80"

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/migrations/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```
