import app.delivery.models  # noqa: F401
import app.projects.models  # noqa: F401

# Ensure all models are registered with Base.metadata for create_all
import app.structure.models  # noqa: F401
from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
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
    app.include_router(delivery_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override
    return app


def _pid(c: TestClient) -> str:
    return c.post("/api/v1/projects", json={"name": "P"}).json()["id"]


def _fid(c: TestClient, pid: str, name: str = "F") -> str:
    return c.post(f"/api/v1/projects/{pid}/features", json={"name": name}).json()["id"]


def _tid(c: TestClient, fid: str) -> str:
    return c.post(f"/api/v1/features/{fid}/tasks", json={"title": "T"}).json()["id"]


# ── Feature ──


def test_create_feature() -> None:
    c = TestClient(_app())
    pid = _pid(c)
    resp = c.post(f"/api/v1/projects/{pid}/features", json={"name": "Auth"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Auth"


def test_get_feature() -> None:
    c = TestClient(_app())
    fid = _fid(c, _pid(c))
    assert c.get(f"/api/v1/features/{fid}").status_code == 200


def test_update_feature() -> None:
    c = TestClient(_app())
    fid = _fid(c, _pid(c))
    resp = c.patch(f"/api/v1/features/{fid}", json={"name": "Auth v2"})
    assert resp.json()["name"] == "Auth v2"


def test_delete_feature() -> None:
    c = TestClient(_app())
    fid = _fid(c, _pid(c))
    assert c.delete(f"/api/v1/features/{fid}").status_code == 204
    assert c.get(f"/api/v1/features/{fid}").status_code == 404


def test_list_features() -> None:
    c = TestClient(_app())
    pid = _pid(c)
    for i in range(3):
        c.post(f"/api/v1/projects/{pid}/features", json={"name": f"F{i}"})
    assert c.get(f"/api/v1/projects/{pid}/features").json()["total"] == 3


def test_feature_not_found() -> None:
    assert TestClient(_app()).get("/api/v1/features/x").status_code == 404


# ── Task ──


def test_create_task() -> None:
    c = TestClient(_app())
    fid = _fid(c, _pid(c))
    resp = c.post(f"/api/v1/features/{fid}/tasks", json={"title": "Implement"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "Implement"


def test_get_task() -> None:
    c = TestClient(_app())
    tid = _tid(c, _fid(c, _pid(c)))
    assert c.get(f"/api/v1/tasks/{tid}").status_code == 200


def test_update_task() -> None:
    c = TestClient(_app())
    tid = _tid(c, _fid(c, _pid(c)))
    resp = c.patch(f"/api/v1/tasks/{tid}", json={"title": "Updated Title"})
    assert resp.json()["title"] == "Updated Title"


def test_delete_task() -> None:
    c = TestClient(_app())
    tid = _tid(c, _fid(c, _pid(c)))
    assert c.delete(f"/api/v1/tasks/{tid}").status_code == 204


def test_list_tasks() -> None:
    c = TestClient(_app())
    fid = _fid(c, _pid(c))
    for i in range(3):
        c.post(f"/api/v1/features/{fid}/tasks", json={"title": f"T{i}"})
    assert c.get(f"/api/v1/features/{fid}/tasks").json()["total"] == 3


# ── Subtask ──


def test_create_subtask() -> None:
    c = TestClient(_app())
    tid = _tid(c, _fid(c, _pid(c)))
    resp = c.post(f"/api/v1/tasks/{tid}/subtasks", json={"title": "Write test"})
    assert resp.status_code == 201


def test_get_subtask() -> None:
    c = TestClient(_app())
    tid = _tid(c, _fid(c, _pid(c)))
    sid = c.post(f"/api/v1/tasks/{tid}/subtasks", json={"title": "S"}).json()["id"]
    assert c.get(f"/api/v1/subtasks/{sid}").status_code == 200


def test_update_subtask() -> None:
    c = TestClient(_app())
    tid = _tid(c, _fid(c, _pid(c)))
    sid = c.post(f"/api/v1/tasks/{tid}/subtasks", json={"title": "S"}).json()["id"]
    resp = c.patch(f"/api/v1/subtasks/{sid}", json={"status": "done"})
    assert resp.json()["status"] == "done"


def test_delete_subtask() -> None:
    c = TestClient(_app())
    tid = _tid(c, _fid(c, _pid(c)))
    sid = c.post(f"/api/v1/tasks/{tid}/subtasks", json={"title": "S"}).json()["id"]
    assert c.delete(f"/api/v1/subtasks/{sid}").status_code == 204


def test_list_subtasks() -> None:
    c = TestClient(_app())
    tid = _tid(c, _fid(c, _pid(c)))
    for i in range(3):
        c.post(f"/api/v1/tasks/{tid}/subtasks", json={"title": f"S{i}"})
    assert c.get(f"/api/v1/tasks/{tid}/subtasks").json()["total"] == 3


# ── Project-level tasks ──


def test_list_tasks_by_project() -> None:
    """GET /projects/{pid}/tasks returns all tasks across features."""
    c = TestClient(_app())
    pid = _pid(c)
    f1 = _fid(c, pid, "F1")
    f2 = _fid(c, pid, "F2")
    c.post(f"/api/v1/features/{f1}/tasks", json={"title": "T1"})
    c.post(f"/api/v1/features/{f1}/tasks", json={"title": "T2"})
    c.post(f"/api/v1/features/{f2}/tasks", json={"title": "T3"})
    resp = c.get(f"/api/v1/projects/{pid}/tasks")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_list_tasks_by_project_empty() -> None:
    """GET /projects/{pid}/tasks returns empty for project with no tasks."""
    c = TestClient(_app())
    pid = _pid(c)
    _fid(c, pid)  # feature exists but no tasks
    resp = c.get(f"/api/v1/projects/{pid}/tasks")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["items"] == []


def test_list_tasks_by_project_pagination() -> None:
    """GET /projects/{pid}/tasks respects offset/limit."""
    c = TestClient(_app())
    pid = _pid(c)
    fid = _fid(c, pid)
    for i in range(5):
        c.post(f"/api/v1/features/{fid}/tasks", json={"title": f"T{i}"})
    resp = c.get(f"/api/v1/projects/{pid}/tasks?offset=2&limit=2")
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["offset"] == 2
    assert body["limit"] == 2


def test_list_tasks_by_project_filter_status() -> None:
    """GET /projects/{pid}/tasks?status=backlog filters by status."""
    c = TestClient(_app())
    pid = _pid(c)
    fid = _fid(c, pid)
    c.post(f"/api/v1/features/{fid}/tasks", json={"title": "Backlog", "status": "backlog"})
    c.post(f"/api/v1/features/{fid}/tasks", json={"title": "Done", "status": "done"})
    resp = c.get(f"/api/v1/projects/{pid}/tasks?status=backlog")
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Backlog"


def test_list_tasks_by_project_filter_feature() -> None:
    """GET /projects/{pid}/tasks?feature_id=X filters by feature."""
    c = TestClient(_app())
    pid = _pid(c)
    f1 = _fid(c, pid, "F1")
    f2 = _fid(c, pid, "F2")
    c.post(f"/api/v1/features/{f1}/tasks", json={"title": "In F1"})
    c.post(f"/api/v1/features/{f2}/tasks", json={"title": "In F2"})
    resp = c.get(f"/api/v1/projects/{pid}/tasks?feature_id=" + f1)
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "In F1"


def test_list_tasks_by_project_filter_assignee() -> None:
    """GET /projects/{pid}/tasks?assignee_type=agent filters by assignee type."""
    c = TestClient(_app())
    pid = _pid(c)
    fid = _fid(c, pid)
    c.post(
        f"/api/v1/features/{fid}/tasks",
        json={"title": "Agent task", "assignee_type": "agent", "assignee_id": "code-guard"},
    )
    c.post(f"/api/v1/features/{fid}/tasks", json={"title": "Unassigned"})
    resp = c.get(f"/api/v1/projects/{pid}/tasks?assignee_type=agent")
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Agent task"
