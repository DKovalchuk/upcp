# Test Plan — UPCP v2

> Project: UPCP | Status: Draft | Updated: 2026-07-27

## 1. Overview

Testing UPCP v2 follows the testing pyramid: many unit tests, fewer integration tests, minimum E2E.

```
        ╱╲
       ╱E2E╲         ← 5-10 critical flows
      ╱──────╲
     ╱ Integr.╲      ← API + DB, MCP contract
    ╱──────────╲
   ╱   Unit     ╲    ← Backend: pytest, Frontend: vitest
  ╱──────────────╲
```

## 2. Unit Tests

### 2.1 Backend (pytest)

**Location:** `tests/unit/`
**Configuration:** `pyproject.toml [tool.pytest]`
**Run:** `make test-unit` or `pytest tests/unit/ -v`

| Module | What is tested | Goal |
|--------|----------------|------|
| `auth/` | JWT creation, validation, password hashing | 100% branches |
| `models/` | ORM mapping, constraints, defaults | all fields |
| `schemas/` | Pydantic validation, edge cases | 100% validators |
| `services/` | Business logic, state transitions | 100% happy + error paths |
| `rate_limit/` | Sliding window, whitelist | all limits |
| `evidence/` | Hash computation, completeness calc | 100% |
| `review/` | Round management, finding creation | 100% |

**Example:**
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

**Location:** `frontend/src/__tests__/`
**Configuration:** `frontend/vitest.config.ts`
**Run:** `cd frontend && npm test`

| Module | What is tested | Goal |
|--------|----------------|------|
| `components/` | Rendering, interactions, props | 100% |
| `hooks/` | Custom hooks, state logic | 100% |
| `store/` | State management, actions | 100% |
| `utils/` | Pure functions, formatters | 100% |
| `api/` | API client, error handling | mock responses |

### 2.3 Coverage targets

| Component | Target | Minimum |
|-----------|--------|---------|
| Backend services | 90% | 80% |
| Backend schemas | 100% | 90% |
| Frontend components | 80% | 60% |
| Frontend hooks | 90% | 80% |

## 3. Integration Tests

### 3.1 API Integration

**Location:** `tests/integration/`
**Environment:** Test PostgreSQL (docker-compose.test.yml)
**Run:** `make test-integration`

**What is tested:**
- CRUD operations via HTTP → DB
- Auth flow: register → login → access → refresh
- RBAC: permission verification for each role
- Rate limiting: receiving 429 when limit exceeded
- Error handling: correct HTTP status codes

**Example:**
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

**What is tested:**
- Migrations: up + down + up
- Foreign key constraints
- Unique constraints
- Indexes
- Cascade deletes

```python
# tests/integration/test_migrations.py
class TestMigrations:
    async def test_migrate_up(self):
        await alembic.upgrade("head")
        # Verify that all tables are created

    async def test_migrate_down_and_up(self):
        await alembic.upgrade("head")
        await alembic.downgrade("-1")
        await alembic.upgrade("head")
        # Data is not lost, schema is correct
```

## 4. E2E Tests

**Location:** `tests/e2e/`
**Tool:** Playwright (frontend) + httpx (backend)
**Run:** `make test-e2e`

### 4.1 Critical flows

| # | Flow | Description |
|---|------|----------|
| 1 | First run | Setup → project → task → claim → evidence → review → done |
| 2 | Agent auth | API key → claim → heartbeat → clarification → resolve |
| 3 | Attention dashboard | Open → see blocked → drill-down → answer → verify |

### 4.2 Smoke tests

```bash
# Minimal smoke test after deploy
make smoke-test
# Checks: health, auth, CRUD
```

## 5. MCP Contract Tests

See [mcp-contract-tests.md](./mcp-contract-tests.md) for details.

**Location:** `tests/mcp/`
**Run:** `make test-mcp`

## 6. Permission Matrix Tests

See [permission-matrix-tests.md](./permission-matrix-tests.md) for details.

**Location:** `tests/permissions/`
**Run:** `make test-permissions`

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

### 7.3 Docker Compose for tests

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
      - /var/lib/postgresql/data  # RAM disk for speed
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
