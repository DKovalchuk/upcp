"""Integration tests for agent detail endpoints — TASK-0099 B5, B6."""

import hashlib
import uuid

import app.audit.models  # noqa: F401
import app.auth.models  # noqa: F401
import app.gitread.models  # noqa: F401
import app.identity.agents  # noqa: F401
import app.identity.models  # noqa: F401
import app.identity.rbac  # noqa: F401
import app.quality.models  # noqa: F401
import app.reporting.models  # noqa: F401
import pytest
from app.delivery.models import (
    Feature,
    Task,
)
from app.identity.agent_endpoints import router
from app.identity.agents import Agent, AgentToken
from app.identity.auth import get_current_user
from app.identity.dependencies import CurrentUser
from app.identity.models import User
from app.projects.models import Project
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from app.shared.text import new_id
from app.structure.models import Component, Module  # noqa: F401
from fastapi.testclient import TestClient

from tests.conftest import _override_session, _test_engine, _TestSession


def _make_app():
    from fastapi import FastAPI

    _app = FastAPI()
    register_error_handlers(_app)
    _app.include_router(router, prefix="/api/v1")
    _app.dependency_overrides[get_session] = _override_session
    _app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id="test-user", email="test@test.com", is_superuser=True
    )
    return _app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    _app = _make_app()
    uid = uuid.uuid4().hex[:8]
    session = _TestSession()
    try:
        user = User(id=f"u-{uid}", email=f"t-{uid}@x.com", password_hash="x", display_name="T")
        session.add(user)
        session.flush()
        # Create the mock current user so ownership checks can verify superuser status
        mock_user = User(
            id="test-user",
            email="test@test.com",
            password_hash="x",
            display_name="Test",
            is_superuser=True,
        )
        session.merge(mock_user)
        session.flush()
        p = Project(name=f"P-{uid}", slug=f"p-{uid}")
        session.add(p)
        session.flush()
        f = Feature(project_id=p.id, name="F1", slug="f1")
        session.add(f)
        session.flush()
        t = Task(feature_id=f.id, title="T1", status="ready")
        session.add(t)
        session.flush()
        agent = Agent(name=f"A-{uid}", description="test agent", created_by=f"u-{uid}")
        session.add(agent)
        session.flush()
        th = hashlib.sha256(f"tok-{uid}".encode()).hexdigest()
        tok = AgentToken(id=f"tok-{uid}", agent_id=agent.id, token_hash=th, name="default")
        session.add(tok)
        session.commit()

        result = {"task_id": t.id, "agent_id": agent.id, "token": f"tok-{uid}"}
        session.close()
    except Exception:
        session.rollback()
        session.close()
        raise
    yield TestClient(_app), result
    try:
        s = _TestSession()
        s.query(AgentToken).filter(AgentToken.id.like("tok-%")).delete(synchronize_session=False)
        s.query(Agent).filter(Agent.name.like("A-%")).delete(synchronize_session=False)
        s.query(User).filter(User.id.in_(["test-user"])).delete(synchronize_session=False)
        s.query(User).filter(User.id.like("u-%")).delete(synchronize_session=False)
        s.query(Project).filter(Project.slug.like("p-%")).delete(synchronize_session=False)
        s.commit()
        s.close()
    except Exception:
        pass


class TestAgentMetrics:
    def test_get_agent_has_metrics(self, client):
        c, data = client
        resp = c.get(f"/api/v1/agents/{data['agent_id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert "metrics" in body
        m = body["metrics"]
        assert "tasks_completed" in m
        assert "tasks_failed" in m
        assert "success_rate" in m
        assert "status" in m
        assert "is_stale" in m

    def test_agent_idle_status(self, client):
        c, data = client
        resp = c.get(f"/api/v1/agents/{data['agent_id']}")
        body = resp.json()
        assert body["metrics"]["status"] == "idle"

    def test_agent_working_status(self, client):
        c, data = client
        task_id = data["task_id"]
        agent_id = data["agent_id"]
        # Create claim directly in DB (workflow router not in this test app)
        session = _TestSession()
        try:
            from datetime import UTC, datetime

            from app.delivery.models import Heartbeat, TaskClaim

            claim = TaskClaim(
                id=new_id(),
                task_id=task_id,
                agent_id=agent_id,
                state="active",
                last_heartbeat_at=datetime.now(UTC),
            )
            session.add(claim)
            session.flush()
            hb = Heartbeat(
                id=new_id(),
                claim_id=claim.id,
                progress_percent=50,
                current_step="coding",
                next_step="testing",
            )
            session.add(hb)
            session.commit()
        finally:
            session.close()

        resp = c.get(f"/api/v1/agents/{agent_id}")
        body = resp.json()
        assert body["metrics"]["status"] == "working"
        assert body["metrics"]["current_task_id"] == task_id

    def test_agent_404(self, client):
        c, _ = client
        resp = c.get("/api/v1/agents/nonexistent")
        assert resp.status_code == 404


class TestAgentClaims:
    def test_get_claims(self, client):
        c, data = client
        resp = c.get(f"/api/v1/agents/{data['agent_id']}/claims")
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_get_claims_after_claim(self, client):
        c, data = client
        # Create claim directly in DB
        session = _TestSession()
        try:
            from app.delivery.models import TaskClaim

            claim = TaskClaim(
                id=new_id(),
                task_id=data["task_id"],
                agent_id=data["agent_id"],
                state="active",
            )
            session.add(claim)
            session.commit()
        finally:
            session.close()

        resp = c.get(f"/api/v1/agents/{data['agent_id']}/claims")
        items = resp.json()["items"]
        assert len(items) >= 1
        assert items[0]["task_id"] == data["task_id"]

    def test_claims_404(self, client):
        c, _ = client
        resp = c.get("/api/v1/agents/nonexistent/claims")
        assert resp.status_code == 404


class TestAgentActivity:
    def test_get_activity_empty(self, client):
        c, data = client
        resp = c.get(f"/api/v1/agents/{data['agent_id']}/activity")
        assert resp.status_code == 200
        assert resp.json()["items"] == []


class TestAgentClarifications:
    def test_get_clarifications_empty(self, client):
        c, data = client
        resp = c.get(f"/api/v1/agents/{data['agent_id']}/clarifications")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_clarifications_404(self, client):
        c, _ = client
        resp = c.get("/api/v1/agents/nonexistent/clarifications")
        assert resp.status_code == 404
