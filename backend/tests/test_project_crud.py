from app.api.v1.projects import router
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=_test_engine)


def _override_session():
    session = TestSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _test_app() -> FastAPI:
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    return app


# ── Create ──

def test_create_project_returns_201() -> None:
    client = TestClient(_test_app())
    resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Project"
    assert data["slug"] == "test-project"
    assert data["status"] == "active"
    assert "id" in data


def test_create_project_with_custom_slug() -> None:
    client = TestClient(_test_app())
    resp = client.post("/api/v1/projects", json={"name": "X", "slug": "my-slug"})
    assert resp.status_code == 201
    assert resp.json()["slug"] == "my-slug"


def test_create_project_duplicate_slug_returns_409() -> None:
    app = _test_app()
    client = TestClient(app)
    client.post("/api/v1/projects", json={"name": "A", "slug": "dup"})
    resp = client.post("/api/v1/projects", json={"name": "B", "slug": "dup"})
    assert resp.status_code == 409


def test_create_project_missing_name_returns_422() -> None:
    client = TestClient(_test_app())
    resp = client.post("/api/v1/projects", json={})
    assert resp.status_code == 422


# ── Read ──

def test_get_project_returns_200() -> None:
    app = _test_app()
    client = TestClient(app)
    pid = client.post("/api/v1/projects", json={"name": "X"}).json()["id"]
    resp = client.get(f"/api/v1/projects/{pid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "X"


def test_get_project_not_found_returns_404() -> None:
    client = TestClient(_test_app())
    resp = client.get("/api/v1/projects/nonexistent")
    assert resp.status_code == 404


# ── Update ──

def test_update_project_returns_200() -> None:
    app = _test_app()
    client = TestClient(app)
    pid = client.post("/api/v1/projects", json={"name": "X"}).json()["id"]
    resp = client.patch(f"/api/v1/projects/{pid}", json={"name": "Y"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Y"


def test_update_project_not_found_returns_404() -> None:
    client = TestClient(_test_app())
    resp = client.patch("/api/v1/projects/nonexistent", json={"name": "Y"})
    assert resp.status_code == 404


# ── Delete ──

def test_delete_project_returns_204() -> None:
    app = _test_app()
    client = TestClient(app)
    pid = client.post("/api/v1/projects", json={"name": "X"}).json()["id"]
    resp = client.delete(f"/api/v1/projects/{pid}")
    assert resp.status_code == 204


def test_delete_project_not_found_returns_404() -> None:
    client = TestClient(_test_app())
    resp = client.delete("/api/v1/projects/nonexistent")
    assert resp.status_code == 404


# ── List ──

def test_list_projects_returns_paginated() -> None:
    app = _test_app()
    client = TestClient(app)
    for i in range(5):
        client.post("/api/v1/projects", json={"name": f"P{i}"})
    resp = client.get("/api/v1/projects?limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["limit"] == 2


def test_list_projects_filter_by_status() -> None:
    app = _test_app()
    client = TestClient(app)
    client.post("/api/v1/projects", json={"name": "A", "status": "active"})
    client.post("/api/v1/projects", json={"name": "B", "status": "archived"})
    resp = client.get("/api/v1/projects?status=archived")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "B"


def test_list_projects_search_by_name() -> None:
    app = _test_app()
    client = TestClient(app)
    client.post("/api/v1/projects", json={"name": "Alpha"})
    client.post("/api/v1/projects", json={"name": "Beta"})
    resp = client.get("/api/v1/projects?search=alph")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Alpha"


def test_list_projects_sort_by_name_asc() -> None:
    app = _test_app()
    client = TestClient(app)
    client.post("/api/v1/projects", json={"name": "Charlie"})
    client.post("/api/v1/projects", json={"name": "Alpha"})
    client.post("/api/v1/projects", json={"name": "Bravo"})
    resp = client.get("/api/v1/projects?sort_by=name&sort_dir=asc")
    names = [p["name"] for p in resp.json()["items"]]
    assert names == ["Alpha", "Bravo", "Charlie"]
