"""API tests for analytics endpoints — TASK-0102 (AC: 5+ API tests)."""

from datetime import UTC, datetime

from app.api.v1.analytics import router as analytics_router
from app.delivery.models import Feature, Task, TaskClaim
from app.projects.models import Project
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from app.shared.text import new_id
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _override_session, _test_engine
from tests.conftest import _TestSession as TestSessionLocal


def _test_app() -> FastAPI:
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(analytics_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    return app


def _seed_project_with_claims(agents: list[str]) -> tuple[str, list[str]]:
    """Create a project with one task + claim per agent. Returns (project_id, task_ids)."""
    session = TestSessionLocal()
    try:
        now = datetime.now(UTC)
        pid, fid = new_id(), new_id()
        session.add(Project(id=pid, name="Analytics", slug="analytics", status="active"))
        # Shared conftest engine enforces PRAGMA foreign_keys, and without a
        # relationship() SQLAlchemy does not order parent/child inserts — the
        # project row must be flushed before the feature that references it.
        session.flush()
        session.add(Feature(id=fid, project_id=pid, name="F1", slug="f1", status="active"))
        session.commit()
        task_ids: list[str] = []
        for aid in agents:
            tid = new_id()
            session.add(
                Task(
                    id=tid,
                    feature_id=fid,
                    title=f"Task {aid}",
                    status="done",
                    created_at=now,
                    updated_at=now,
                )
            )
            session.add(
                TaskClaim(
                    id=new_id(),
                    task_id=tid,
                    agent_id=aid,
                    claimed_at=now,
                )
            )
            task_ids.append(tid)
        session.commit()
        return pid, task_ids
    finally:
        session.close()


def test_project_trends_returns_default_weeks() -> None:
    client = TestClient(_test_app())
    pid, _ = _seed_project_with_claims([])

    resp = client.get(f"/api/v1/analytics/project/{pid}/trends")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 8  # default weeks=8
    assert {"week", "completed", "created"} <= items[0].keys()


def test_project_velocity_returns_default_weeks() -> None:
    client = TestClient(_test_app())
    pid, _ = _seed_project_with_claims([])

    resp = client.get(f"/api/v1/analytics/project/{pid}/velocity")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 8
    assert {"week", "count"} <= items[0].keys()


def test_health_history_returns_default_days() -> None:
    client = TestClient(_test_app())
    pid, _ = _seed_project_with_claims([])

    resp = client.get(f"/api/v1/analytics/project/{pid}/health-history")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 30  # default days=30
    assert {"date", "completed", "created", "score"} <= items[0].keys()


def test_global_velocity_respects_weeks_param() -> None:
    client = TestClient(_test_app())
    _seed_project_with_claims([])

    resp = client.get("/api/v1/analytics/velocity", params={"weeks": 2})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    assert {"week", "count"} <= items[0].keys()


def test_agent_performance_returns_metrics() -> None:
    client = TestClient(_test_app())
    _seed_project_with_claims(["agent-1", "agent-2"])

    resp = client.get("/api/v1/analytics/agent/agent-1/performance")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["agent_id"] == "agent-1"
    assert items[0]["total_claims"] == 1
    assert "success_rate" in items[0]
    assert "avg_hours" in items[0]


def test_agents_overview_is_paginated() -> None:
    client = TestClient(_test_app())
    _seed_project_with_claims(["agent-1", "agent-2", "agent-3"])

    resp = client.get("/api/v1/analytics/agents/overview", params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert [i["agent_id"] for i in data["items"]] == ["agent-1", "agent-2"]

    resp2 = client.get("/api/v1/analytics/agents/overview", params={"limit": 2, "offset": 1})
    data2 = resp2.json()
    assert data2["total"] == 3
    assert [i["agent_id"] for i in data2["items"]] == ["agent-2", "agent-3"]
