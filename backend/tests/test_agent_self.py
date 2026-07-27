"""Tests for agent self-service endpoints — TASK-0075."""

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
from app.api.v1.agent_self import router
from app.delivery.models import Feature, Task  # noqa: F401
from app.identity.agents import Agent, AgentToken  # noqa: F401
from app.identity.models import User  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from app.structure.models import Component, Module  # noqa: F401
from fastapi.testclient import TestClient

from tests.conftest import _override_session, _test_engine, _TestSession

_RAW_TOKEN = "test-token-agent-self"


def _make_app():
    from fastapi import FastAPI

    _app = FastAPI()
    register_error_handlers(_app)
    _app.include_router(router, prefix="/api/v1")
    _app.dependency_overrides[get_session] = _override_session
    return _app


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=_test_engine)
    _app = _make_app()
    uid = uuid.uuid4().hex[:8]
    session = _TestSession()
    try:
        user = User(id=f"u-{uid}", email=f"t-{uid}@x.com", password_hash="x", display_name="T")
        session.add(user)
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
        agent = Agent(name=f"A-{uid}", description="test", created_by=f"u-{uid}")
        session.add(agent)
        session.flush()
        th = hashlib.sha256(_RAW_TOKEN.encode()).hexdigest()
        tok = AgentToken(
            id=f"tok-{uid}",
            agent_id=agent.id,
            token_hash=th,
            name="t",
            scopes={"read": True, "write": True},
        )
        session.add(tok)
        session.commit()
        session.close()
    except Exception:
        session.rollback()
        session.close()
        raise
    yield TestClient(_app)
    try:
        s = _TestSession()
        s.query(AgentToken).filter(AgentToken.id.like("tok-%")).delete(synchronize_session=False)
        s.query(Agent).filter(Agent.name.like("A-%")).delete(synchronize_session=False)
        s.query(User).filter(User.id.like("u-%")).delete(synchronize_session=False)
        s.query(Project).filter(Project.slug.like("p-%")).delete(synchronize_session=False)
        s.commit()
        s.close()
    except Exception:
        pass


def _hdr():
    return {"X-Agent-Token": _RAW_TOKEN}


class TestAgentMe:
    def test_agent_me_success(self, client):
        resp = client.get("/api/v1/agent/me", headers=_hdr())
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "inbox_count" in data

    def test_agent_me_no_token(self, client):
        resp = client.get("/api/v1/agent/me")
        assert resp.status_code == 401


class TestAgentInbox:
    def test_inbox_empty(self, client):
        resp = client.get("/api/v1/agent/inbox", headers=_hdr())
        assert resp.status_code == 200
        assert resp.json()["events"] == []

    def test_inbox_no_token(self, client):
        resp = client.get("/api/v1/agent/inbox")
        assert resp.status_code == 401


class TestAgentPlaybook:
    def test_playbook_returns_content(self, client):
        resp = client.get("/api/v1/agent/playbook", headers=_hdr())
        assert resp.status_code == 200
        assert len(resp.json()["content"]) > 0

    def test_playbook_no_token(self, client):
        resp = client.get("/api/v1/agent/playbook")
        assert resp.status_code == 401
