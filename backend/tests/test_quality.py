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

_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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


def _task_id(c: TestClient) -> str:
    pid = c.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    fid = c.post(f"/api/v1/projects/{pid}/features", json={"name": "F"}).json()["id"]
    return c.post(f"/api/v1/features/{fid}/tasks", json={"title": "T"}).json()["id"]


# ── Acceptance Criterion ──

def test_create_ac() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    resp = c.post(f"/api/v1/tasks/{tid}/acceptance-criteria", json={"description": "Must work"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


def test_update_ac_status() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    acid = c.post(f"/api/v1/tasks/{tid}/acceptance-criteria", json={"description": "X"}).json()["id"]
    resp = c.patch(f"/api/v1/acceptance-criteria/{acid}", json={"status": "passed"})
    assert resp.json()["status"] == "passed"


def test_delete_ac() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    acid = c.post(f"/api/v1/tasks/{tid}/acceptance-criteria", json={"description": "X"}).json()["id"]
    assert c.delete(f"/api/v1/acceptance-criteria/{acid}").status_code == 204


def test_list_acs() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    c.post(f"/api/v1/tasks/{tid}/acceptance-criteria", json={"description": "A"})
    c.post(f"/api/v1/tasks/{tid}/acceptance-criteria", json={"description": "B"})
    assert len(c.get(f"/api/v1/tasks/{tid}/acceptance-criteria").json()) == 2


# ── DoD Item ──

def test_create_dod() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    resp = c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "Tests pass"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


def test_update_dod_status() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    did = c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "X"}).json()["id"]
    resp = c.patch(f"/api/v1/dod-items/{did}", json={"status": "passed"})
    assert resp.json()["status"] == "passed"


def test_delete_dod() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    did = c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "X"}).json()["id"]
    assert c.delete(f"/api/v1/dod-items/{did}").status_code == 204


def test_list_dods() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "A"})
    assert len(c.get(f"/api/v1/tasks/{tid}/dod-items").json()) == 1


# ── Quality Gate ──

def test_complete_task_with_all_dod_passed() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    did = c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "X"}).json()["id"]
    c.patch(f"/api/v1/dod-items/{did}", json={"status": "passed"})
    resp = c.post(f"/api/v1/tasks/{tid}/complete")
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_complete_task_fails_when_dod_not_passed() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "X"})
    resp = c.post(f"/api/v1/tasks/{tid}/complete")
    assert resp.status_code == 400


def test_complete_task_without_dod_succeeds() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    resp = c.post(f"/api/v1/tasks/{tid}/complete")
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
