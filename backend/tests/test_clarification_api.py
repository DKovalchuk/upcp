"""Integration tests for clarification API endpoints — TASK-0099 B1."""

import hashlib
import uuid

import app.audit.models  # noqa: F401
import app.gitread.models  # noqa: F401
import app.identity.agents  # noqa: F401
import app.identity.models  # noqa: F401
import app.identity.rbac  # noqa: F401
import app.quality.models  # noqa: F401
import app.reporting.models  # noqa: F401
import pytest
from app.api.v1.task_workflow import router
from app.delivery.models import Feature, Task
from app.identity.agents import Agent, AgentToken
from app.identity.models import User
from app.projects.models import Project
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from app.shared.text import new_id
from app.structure.models import Component, Module  # noqa: F401
from fastapi.testclient import TestClient

from tests.conftest import _override_session, _test_engine, _TestSession

_RAW_TOKEN = "test-token-cl"


def _make_app():
    from fastapi import FastAPI

    _app = FastAPI()
    register_error_handlers(_app)
    _app.include_router(router, prefix="/api/v1")
    _app.dependency_overrides[get_session] = _override_session
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
        p = Project(name=f"P-{uid}", slug=f"p-{uid}")
        session.add(p)
        session.flush()
        f = Feature(project_id=p.id, name="F1", slug="f1")
        session.add(f)
        session.flush()
        t = Task(feature_id=f.id, title="T1", status="in_progress")
        session.add(t)
        session.flush()
        agent = Agent(name=f"A-{uid}", description="test", created_by=f"u-{uid}")
        session.add(agent)
        session.flush()
        th = hashlib.sha256(f"{_RAW_TOKEN}-{uid}".encode()).hexdigest()
        tok = AgentToken(id=f"tok-{uid}", agent_id=agent.id, token_hash=th, name="t")
        session.add(tok)
        # Create active claim
        from app.delivery.models import TaskClaim

        claim = TaskClaim(
            id=new_id(),
            task_id=t.id,
            agent_id=agent.id,
            state="active",
        )
        session.add(claim)
        session.commit()

        result = {"task_id": t.id, "agent_id": agent.id, "token": f"{_RAW_TOKEN}-{uid}"}
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
        s.query(User).filter(User.id.like("u-%")).delete(synchronize_session=False)
        s.query(Project).filter(Project.slug.like("p-%")).delete(synchronize_session=False)
        s.commit()
        s.close()
    except Exception:
        pass


def _hdr(token: str | None = None) -> dict[str, str]:
    return {"X-Agent-Token": token or _RAW_TOKEN}


class TestCreateClarificationEndpoint:
    def test_create_success(self, client):
        c, data = client
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/clarifications",
            headers=_hdr(data["token"]),
            json={"question": "What format?", "blocking": False},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["question"] == "What format?"
        assert body["state"] == "open"

    def test_create_blocking(self, client):
        c, data = client
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/clarifications",
            headers=_hdr(data["token"]),
            json={"question": "Important?", "blocking": True},
        )
        assert resp.status_code == 201
        assert resp.json()["blocking"] is True

    def test_create_no_token(self, client):
        c, data = client
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/clarifications",
            json={"question": "Q?"},
        )
        assert resp.status_code == 401

    def test_create_404_task(self, client):
        c, data = client
        resp = c.post(
            "/api/v1/tasks/nonexistent/clarifications",
            headers=_hdr(data["token"]),
            json={"question": "Q?"},
        )
        assert resp.status_code == 404


class TestAnswerClarificationEndpoint:
    def _create_clarification(self, c, data) -> str:
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/clarifications",
            headers=_hdr(data["token"]),
            json={"question": "Q?"},
        )
        return resp.json()["id"]

    def test_answer_success(self, client):
        c, data = client
        cr_id = self._create_clarification(c, data)
        resp = c.post(
            f"/api/v1/clarifications/{cr_id}/answer",
            headers=_hdr(data["token"]),
            json={"answer": "Use JSON format"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "answered"
        assert body["answer"] == "Use JSON format"

    def test_answer_no_token(self, client):
        c, data = client
        cr_id = self._create_clarification(c, data)
        resp = c.post(
            f"/api/v1/clarifications/{cr_id}/answer",
            json={"answer": "x"},
        )
        assert resp.status_code == 401

    def test_answer_404(self, client):
        c, data = client
        resp = c.post(
            "/api/v1/clarifications/nonexistent/answer",
            headers=_hdr(data["token"]),
            json={"answer": "x"},
        )
        assert resp.status_code == 404
