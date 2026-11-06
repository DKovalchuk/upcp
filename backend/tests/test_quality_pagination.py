"""Tests for quality endpoints pagination — TASK-0092 (2.3)."""

# Import all models to ensure tables are created
import app.audit.models  # noqa: F401
import app.delivery.models  # noqa: F401
import app.gitread.models  # noqa: F401
import app.identity.agents  # noqa: F401
import app.identity.models  # noqa: F401
import app.identity.rbac  # noqa: F401
import app.projects.models  # noqa: F401
import app.quality.models  # noqa: F401
import app.reporting.models  # noqa: F401
import app.structure.models  # noqa: F401
from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.structure import router as structure_router
from app.delivery.models import Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _override_session, _test_engine


def _test_app() -> FastAPI:
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(structure_router, prefix="/api/v1")
    app.include_router(delivery_router, prefix="/api/v1")
    app.include_router(quality_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    return app


def _seed_data(client: TestClient) -> dict:
    """Create project, feature, task for testing."""
    # Create project
    resp = client.post("/api/v1/projects", json={"name": "Test"})
    project = resp.json()

    # Create feature
    resp = client.post(
        f"/api/v1/projects/{project['id']}/features",
        json={"name": "F1", "slug": "f1"},
    )
    feature = resp.json()

    # Create task
    resp = client.post(
        f"/api/v1/features/{feature['id']}/tasks",
        json={"title": "T1"},
    )
    task = resp.json()

    return {"project": project, "feature": feature, "task": task}


class TestACPagination:
    def test_list_acs_returns_paginated(self):
        """list_acs returns paginated response with total."""
        client = TestClient(_test_app())
        data = _seed_data(client)

        # Create 5 ACs
        for i in range(5):
            client.post(
                f"/api/v1/tasks/{data['task']['id']}/acceptance-criteria",
                json={"description": f"AC-{i}"},
            )

        # List with pagination
        resp = client.get(
            f"/api/v1/tasks/{data['task']['id']}/acceptance-criteria",
            params={"offset": 0, "limit": 2},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert body["total"] == 5
        assert len(body["items"]) == 2
        assert body["offset"] == 0
        assert body["limit"] == 2

    def test_list_acs_default_pagination(self):
        """list_acs without params returns all items."""
        client = TestClient(_test_app())
        data = _seed_data(client)

        for i in range(3):
            client.post(
                f"/api/v1/tasks/{data['task']['id']}/acceptance-criteria",
                json={"description": f"AC-{i}"},
            )

        resp = client.get(f"/api/v1/tasks/{data['task']['id']}/acceptance-criteria")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 3


class TestDoDPagination:
    def test_list_dods_returns_paginated(self):
        """list_dods returns paginated response with total."""
        client = TestClient(_test_app())
        data = _seed_data(client)

        for i in range(4):
            client.post(
                f"/api/v1/tasks/{data['task']['id']}/dod-items",
                json={"name": f"DoD-{i}"},
            )

        resp = client.get(
            f"/api/v1/tasks/{data['task']['id']}/dod-items",
            params={"offset": 0, "limit": 2},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 4
        assert len(body["items"]) == 2


class TestEvidencePagination:
    def test_list_evidence_returns_paginated(self):
        """list_evidence returns paginated response with total."""
        client = TestClient(_test_app())
        data = _seed_data(client)

        for i in range(3):
            client.post(
                f"/api/v1/tasks/{data['task']['id']}/evidence",
                json={
                    "type": "note",
                    "title": f"Evidence-{i}",
                    "created_by_type": "agent",
                    "created_by_id": "test",
                },
            )

        resp = client.get(
            f"/api/v1/tasks/{data['task']['id']}/evidence",
            params={"offset": 0, "limit": 2},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2


class TestReviewRoundPagination:
    def test_list_review_rounds_returns_paginated(self):
        """list_review_rounds returns paginated response with total."""
        client = TestClient(_test_app())
        data = _seed_data(client)

        for i in range(3):
            client.post(
                f"/api/v1/tasks/{data['task']['id']}/review-rounds",
                json={"reviewer_type": "agent", "reviewer_id": f"agent-{i}"},
            )

        resp = client.get(
            f"/api/v1/tasks/{data['task']['id']}/review-rounds",
            params={"offset": 0, "limit": 2},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
