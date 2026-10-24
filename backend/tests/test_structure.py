from app.api.v1.projects import router as projects_router
from app.api.v1.structure import router as structure_router
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _test_engine as _engine

# Shared engine/session from conftest (TASK-0112 engine dedup).
from tests.conftest import _TestSession as _Session


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
    app.dependency_overrides[get_session] = _override
    return app


def _project_id(client: TestClient) -> str:
    return client.post("/api/v1/projects", json={"name": "P"}).json()["id"]


def _component_id(client: TestClient, project_id: str) -> str:
    return client.post(f"/api/v1/projects/{project_id}/components", json={"name": "C"}).json()["id"]


# ── Component CRUD ──


def test_create_component() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    resp = c.post(f"/api/v1/projects/{pid}/components", json={"name": "Auth"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Auth"
    assert resp.json()["project_id"] == pid


def test_get_component() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    cid = _component_id(c, pid)
    resp = c.get(f"/api/v1/components/{cid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == cid


def test_update_component() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    cid = _component_id(c, pid)
    resp = c.patch(f"/api/v1/components/{cid}", json={"name": "Auth v2"})
    assert resp.json()["name"] == "Auth v2"


def test_delete_component() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    cid = _component_id(c, pid)
    assert c.delete(f"/api/v1/components/{cid}").status_code == 204
    assert c.get(f"/api/v1/components/{cid}").status_code == 404


def test_list_components() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    for i in range(3):
        c.post(f"/api/v1/projects/{pid}/components", json={"name": f"C{i}"})
    resp = c.get(f"/api/v1/projects/{pid}/components")
    assert resp.json()["total"] == 3


def test_component_duplicate_slug_returns_409() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    c.post(f"/api/v1/projects/{pid}/components", json={"name": "X", "slug": "dup"})
    resp = c.post(f"/api/v1/projects/{pid}/components", json={"name": "Y", "slug": "dup"})
    assert resp.status_code == 409


# ── Module CRUD ──


def test_create_module() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    cid = _component_id(c, pid)
    resp = c.post(f"/api/v1/components/{cid}/modules", json={"name": "Auth Core"})
    assert resp.status_code == 201
    assert resp.json()["component_id"] == cid


def test_get_module() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    cid = _component_id(c, pid)
    mid = c.post(f"/api/v1/components/{cid}/modules", json={"name": "M"}).json()["id"]
    resp = c.get(f"/api/v1/modules/{mid}")
    assert resp.status_code == 200


def test_update_module() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    cid = _component_id(c, pid)
    mid = c.post(f"/api/v1/components/{cid}/modules", json={"name": "M"}).json()["id"]
    resp = c.patch(f"/api/v1/modules/{mid}", json={"name": "M v2"})
    assert resp.json()["name"] == "M v2"


def test_delete_module() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    cid = _component_id(c, pid)
    mid = c.post(f"/api/v1/components/{cid}/modules", json={"name": "M"}).json()["id"]
    assert c.delete(f"/api/v1/modules/{mid}").status_code == 204
    assert c.get(f"/api/v1/modules/{mid}").status_code == 404


def test_list_modules() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    cid = _component_id(c, pid)
    for i in range(3):
        c.post(f"/api/v1/components/{cid}/modules", json={"name": f"M{i}"})
    resp = c.get(f"/api/v1/components/{cid}/modules")
    assert resp.json()["total"] == 3


def test_module_duplicate_slug_returns_409() -> None:
    c = TestClient(_app())
    pid = _project_id(c)
    cid = _component_id(c, pid)
    c.post(f"/api/v1/components/{cid}/modules", json={"name": "X", "slug": "dup"})
    resp = c.post(f"/api/v1/components/{cid}/modules", json={"name": "Y", "slug": "dup"})
    assert resp.status_code == 409
