from fastapi.testclient import TestClient

from app.api.v1.search import router as search_router
from app.delivery.models import Feature, Task
from app.projects.models import Project
from app.structure.models import Component, Module  # noqa: F401 — ensure FK tables exist
from tests.conftest import _TestSession, make_test_app

app = make_test_app(search_router)
client = TestClient(app)


def _setup_data():
    session = _TestSession()
    p = Project(name="Test Project", slug="test-project", description="A test project", status="active")
    session.add(p)
    session.flush()
    f = Feature(project_id=p.id, name="Auth Feature", slug="auth", description="Authentication", status="backlog")
    session.add(f)
    session.flush()
    t = Task(feature_id=f.id, title="Login page", description="Build login page", status="backlog", priority=0)
    session.add(t)
    session.commit()
    session.close()


_setup_data()


class TestSearch:
    def test_search_projects(self):
        resp = client.get("/api/v1/search?q=Test")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["entity_type"] == "project"
        assert data[0]["title"] == "Test Project"

    def test_search_features(self):
        resp = client.get("/api/v1/search?q=Auth")
        assert resp.status_code == 200
        data = resp.json()
        assert any(r["entity_type"] == "feature" for r in data)

    def test_search_tasks(self):
        resp = client.get("/api/v1/search?q=Login")
        assert resp.status_code == 200
        data = resp.json()
        assert any(r["entity_type"] == "task" for r in data)

    def test_search_no_results(self):
        resp = client.get("/api/v1/search?q=nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_search_limit(self):
        resp = client.get("/api/v1/search?q=Test&limit=1")
        assert resp.status_code == 200
        assert len(resp.json()) <= 1

    def test_search_empty_query(self):
        resp = client.get("/api/v1/search?q=")
        assert resp.status_code == 422
