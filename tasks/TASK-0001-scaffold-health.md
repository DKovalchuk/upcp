# TASK-0001 Scaffold Repository and Health Endpoint

Spec: SPEC-0001
Status: done
Priority: 10
Model: routine
Milestone: M0

## Goal

Create the minimal backend health endpoint and validate the repository scaffold.

## Non-goals

- Do not add database models.
- Do not add auth.
- Do not add frontend.
- Do not add MCP.
- Do not add LLM.
- Do not add Git integration.

## Files likely involved

```text
backend/app/__init__.py
backend/app/main.py
backend/tests/__init__.py
backend/tests/test_health.py
```

## TDD Steps

1. Create failing test `backend/tests/test_health.py`.
2. Run test and confirm failure.
3. Create minimal `backend/app/main.py`.
4. Run test and confirm pass.
5. Run lint and typecheck.
6. Validate Docker Compose.
7. Optionally start app and check health.

## Expected test

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "upcp-backend",
    }
```

## Expected implementation

```python
from fastapi import FastAPI

app = FastAPI(title="UPCP Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "upcp-backend",
    }
```

## Acceptance Criteria

- failing test exists before implementation;
- `GET /health` returns expected payload;
- `make test` passes;
- `make lint` passes;
- `make typecheck` passes;
- `docker compose config` succeeds;
- no secrets are added;
- task status updated;
- PROJECT_STATUS updated.

## Commands

```bash
make test
make lint
make typecheck
docker compose config
cp .env.example .env
docker compose up --build
curl http://127.0.0.1:38080/health
```

## DoD

- test added;
- endpoint added;
- commands pass;
- status updated.
