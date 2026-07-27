from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.structure import router as structure_router
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(bind=_engine)


def _override():
    s = _Session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def _app() -> FastAPI:
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(structure_router, prefix="/api/v1")
    app.include_router(delivery_router, prefix="/api/v1")
    app.include_router(quality_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override
    return app


def _project_with_tasks(c: TestClient, num_tasks: int = 3) -> tuple[str, list[str]]:
    """Create a project with features and tasks, return (project_id, task_ids)."""
    pid = c.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    fid = c.post(f"/api/v1/projects/{pid}/features", json={"name": "F"}).json()["id"]
    task_ids = []
    for i in range(num_tasks):
        tid = c.post(f"/api/v1/features/{fid}/tasks", json={"title": f"T{i}"}).json()["id"]
        task_ids.append(tid)
    return pid, task_ids


# ── Quality Stats ──


def test_quality_stats_empty_project() -> None:
    """Project with no tasks returns zeroed stats."""
    c = TestClient(_app())
    pid = c.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    resp = c.get(f"/api/v1/projects/{pid}/quality/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tasks"] == 0
    assert data["tasks_with_ac"] == 0
    assert data["total_ac"] == 0
    assert data["passed_ac"] == 0
    assert data["total_dod"] == 0
    assert data["passed_dod"] == 0
    assert data["pass_rate"] == 0.0


def test_quality_stats_with_ac() -> None:
    """Tasks with acceptance criteria are counted correctly."""
    c = TestClient(_app())
    pid, task_ids = _project_with_tasks(c, 2)

    # Task 0: 2 ACs, 1 passed
    c.post(f"/api/v1/tasks/{task_ids[0]}/acceptance-criteria", json={"description": "AC1"})
    c.post(f"/api/v1/tasks/{task_ids[0]}/acceptance-criteria", json={"description": "AC2"})
    acs = c.get(f"/api/v1/tasks/{task_ids[0]}/acceptance-criteria").json()
    c.patch(f"/api/v1/acceptance-criteria/{acs[0]['id']}", json={"status": "passed"})

    # Task 1: 1 AC, pending
    c.post(f"/api/v1/tasks/{task_ids[1]}/acceptance-criteria", json={"description": "AC3"})

    resp = c.get(f"/api/v1/projects/{pid}/quality/stats")
    data = resp.json()
    assert data["total_tasks"] == 2
    assert data["tasks_with_ac"] == 2
    assert data["total_ac"] == 3
    assert data["passed_ac"] == 1


def test_quality_stats_with_dod() -> None:
    """Tasks with DoD items are counted correctly."""
    c = TestClient(_app())
    pid, task_ids = _project_with_tasks(c, 2)

    # Task 0: 2 DoD, 2 passed
    c.post(f"/api/v1/tasks/{task_ids[0]}/dod-items", json={"name": "D1"})
    c.post(f"/api/v1/tasks/{task_ids[0]}/dod-items", json={"name": "D2"})
    dods = c.get(f"/api/v1/tasks/{task_ids[0]}/dod-items").json()
    c.patch(f"/api/v1/dod-items/{dods[0]['id']}", json={"status": "passed"})
    c.patch(f"/api/v1/dod-items/{dods[1]['id']}", json={"status": "passed"})

    # Task 1: 1 DoD, pending
    c.post(f"/api/v1/tasks/{task_ids[1]}/dod-items", json={"name": "D3"})

    resp = c.get(f"/api/v1/projects/{pid}/quality/stats")
    data = resp.json()
    assert data["total_tasks"] == 2
    assert data["total_dod"] == 3
    assert data["passed_dod"] == 2


def test_quality_stats_pass_rate() -> None:
    """Pass rate is calculated as (passed_ac + passed_dod) / (total_ac + total_dod) * 100."""
    c = TestClient(_app())
    pid, task_ids = _project_with_tasks(c, 1)

    # 2 ACs (1 passed) + 2 DoD (1 passed) => 2/4 = 50%
    c.post(f"/api/v1/tasks/{task_ids[0]}/acceptance-criteria", json={"description": "AC1"})
    c.post(f"/api/v1/tasks/{task_ids[0]}/acceptance-criteria", json={"description": "AC2"})
    acs = c.get(f"/api/v1/tasks/{task_ids[0]}/acceptance-criteria").json()
    c.patch(f"/api/v1/acceptance-criteria/{acs[0]['id']}", json={"status": "passed"})

    c.post(f"/api/v1/tasks/{task_ids[0]}/dod-items", json={"name": "D1"})
    c.post(f"/api/v1/tasks/{task_ids[0]}/dod-items", json={"name": "D2"})
    dods = c.get(f"/api/v1/tasks/{task_ids[0]}/dod-items").json()
    c.patch(f"/api/v1/dod-items/{dods[0]['id']}", json={"status": "passed"})

    resp = c.get(f"/api/v1/projects/{pid}/quality/stats")
    data = resp.json()
    assert data["total_ac"] == 2
    assert data["passed_ac"] == 1
    assert data["total_dod"] == 2
    assert data["passed_dod"] == 1
    assert data["pass_rate"] == 50.0


def test_quality_stats_pass_rate_zero_items() -> None:
    """Pass rate is 0 when there are no AC or DoD items."""
    c = TestClient(_app())
    pid, _ = _project_with_tasks(c, 1)
    resp = c.get(f"/api/v1/projects/{pid}/quality/stats")
    assert resp.json()["pass_rate"] == 0.0


def test_quality_stats_pass_rate_all_passed() -> None:
    """Pass rate is 100 when all items are passed."""
    c = TestClient(_app())
    pid, task_ids = _project_with_tasks(c, 1)

    c.post(f"/api/v1/tasks/{task_ids[0]}/acceptance-criteria", json={"description": "AC1"})
    acs = c.get(f"/api/v1/tasks/{task_ids[0]}/acceptance-criteria").json()
    c.patch(f"/api/v1/acceptance-criteria/{acs[0]['id']}", json={"status": "passed"})

    c.post(f"/api/v1/tasks/{task_ids[0]}/dod-items", json={"name": "D1"})
    dods = c.get(f"/api/v1/tasks/{task_ids[0]}/dod-items").json()
    c.patch(f"/api/v1/dod-items/{dods[0]['id']}", json={"status": "passed"})

    resp = c.get(f"/api/v1/projects/{pid}/quality/stats")
    assert resp.json()["pass_rate"] == 100.0


def test_quality_stats_project_not_found() -> None:
    """Non-existent project returns 404."""
    c = TestClient(_app())
    resp = c.get("/api/v1/projects/nonexistent/quality/stats")
    assert resp.status_code == 404
