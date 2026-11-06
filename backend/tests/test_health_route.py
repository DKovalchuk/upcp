"""GET /api/v1/projects/{project_id}/health — TASK-0087 AC «Tests».

The route documents a 404 contract (``responses={404: ...}`` in
``app/api/v1/dashboard.py``) but had zero HTTP-level tests, and
``AttentionDashboardService.get_project_health`` returned
``{"score": 100, ...}`` for unknown projects — so the documented 404 never
fired. These tests pin:

1. unknown project → 404 (RED before the dashboard.py fix);
2. existing project without tasks → 200 with the useful default
   (score/breakdown/top_issue) — behavior preserved, not changed;
3. existing project with tasks → 200 with a computed breakdown (regression
   guard for the fix).

Shared conftest helpers only (``make_test_app``) — no local engine or local
``_db`` fixture (see ``test_db_fixture_contract.py``).
"""

from uuid import uuid4

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.structure import router as structure_router
from app.shared.text import new_id
from fastapi.testclient import TestClient

from tests.conftest import make_test_app


def _client() -> TestClient:
    """Fresh app with project/feature/task creation + the health route."""
    return TestClient(
        make_test_app(projects_router, structure_router, delivery_router, dashboard_router)
    )


def test_health_unknown_project_returns_404() -> None:
    """Contract: an unknown project id must 404 — not answer 200 score 100."""
    client = _client()
    resp = client.get(f"/api/v1/projects/{uuid4()}/health")
    assert resp.status_code == 404
    body = resp.json()
    assert "not found" in str(body["detail"]).lower()


def test_health_existing_project_without_tasks_returns_200_default() -> None:
    """Existing project with no tasks keeps the current useful default (200)."""
    client = _client()
    project = client.post("/api/v1/projects", json={"name": "No Tasks"}).json()

    resp = client.get(f"/api/v1/projects/{project['id']}/health")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"score", "breakdown", "top_issue"}
    assert body["score"] == 100
    assert body["breakdown"] == {}
    assert body["top_issue"] == ""


def test_health_existing_project_with_tasks_returns_breakdown() -> None:
    """Existing project with tasks still gets a computed score/breakdown (regression guard)."""
    client = _client()
    project = client.post("/api/v1/projects", json={"name": "Blocked Project"}).json()
    feature = client.post(
        f"/api/v1/projects/{project['id']}/features",
        json={"name": "HF", "slug": f"hf-{new_id()[:8]}"},
    ).json()
    created = client.post(
        f"/api/v1/features/{feature['id']}/tasks",
        json={"title": "Blocked one", "status": "blocked"},
    )
    assert created.status_code == 201

    resp = client.get(f"/api/v1/projects/{project['id']}/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] == 85  # 100 - (1 blocked * 15)
    assert body["breakdown"]["blocked"] == 1
    assert body["top_issue"] == "blocked tasks"
