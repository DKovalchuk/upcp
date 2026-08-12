"""Tests for workflow API endpoints — TASK-0074."""

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
from app.api.v1.task_workflow import router
from app.delivery.models import (
    ClarificationRequest,
    Feature,
    Task,
)
from app.identity.agents import Agent, AgentToken  # noqa: F401
from app.identity.models import User  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from app.shared.text import new_id
from app.structure.models import Component, Module  # noqa: F401
from fastapi.testclient import TestClient

from tests.conftest import _override_session, _test_engine, _TestSession

_RAW_TOKEN = "test-token-wf"


def _make_app():
    """Create app without dropping tables."""
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
        t = Task(feature_id=f.id, title="T1", status="ready")
        session.add(t)
        session.flush()
        agent = Agent(name=f"A-{uid}", description="test", created_by=f"u-{uid}")
        session.add(agent)
        session.flush()
        th = hashlib.sha256(f"{_RAW_TOKEN}-{uid}".encode()).hexdigest()
        tok = AgentToken(id=f"tok-{uid}", agent_id=agent.id, token_hash=th, name="t")
        session.add(tok)
        session.commit()

        result = {"task_id": t.id, "agent_id": agent.id, "token": f"{_RAW_TOKEN}-{uid}"}
        session.close()
    except Exception:
        session.rollback()
        session.close()
        raise
    yield TestClient(_app), result
    # Cleanup: delete test data to avoid interfering with other tests
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


def _hdr(token: str | None = None):
    return {"X-Agent-Token": token or _RAW_TOKEN}


class TestClaimEndpoint:
    def test_claim_success(self, client):
        c, data = client
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/claim",
            headers=_hdr(data["token"]),
            json={"context_snapshot": "s"},
        )
        assert resp.status_code == 201
        assert resp.json()["state"] == "active"

    def test_claim_no_token(self, client):
        c, data = client
        resp = c.post(f"/api/v1/tasks/{data['task_id']}/claim", json={})
        assert resp.status_code == 401

    def test_claim_already_claimed(self, client):
        c, data = client
        c.post(f"/api/v1/tasks/{data['task_id']}/claim", headers=_hdr(data["token"]), json={})
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/claim", headers=_hdr(data["token"]), json={}
        )
        assert resp.status_code == 409


class TestReleaseEndpoint:
    def test_release_success(self, client):
        c, data = client
        c.post(f"/api/v1/tasks/{data['task_id']}/claim", headers=_hdr(data["token"]), json={})
        resp = c.post(f"/api/v1/tasks/{data['task_id']}/release", headers=_hdr(data["token"]))
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_release_no_claim(self, client):
        c, data = client
        resp = c.post(f"/api/v1/tasks/{data['task_id']}/release", headers=_hdr(data["token"]))
        assert resp.status_code == 404


class TestHeartbeatEndpoint:
    def test_heartbeat_success(self, client):
        c, data = client
        c.post(f"/api/v1/tasks/{data['task_id']}/claim", headers=_hdr(data["token"]), json={})
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/heartbeat",
            headers=_hdr(data["token"]),
            json={"progress_percent": 50, "current_step": "c", "next_step": "t"},
        )
        assert resp.status_code == 200

    def test_heartbeat_no_claim(self, client):
        c, data = client
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/heartbeat",
            headers=_hdr(data["token"]),
            json={"progress_percent": 50, "current_step": "c", "next_step": "t"},
        )
        assert resp.status_code == 404


class TestProgressEndpoint:
    def test_progress_success(self, client):
        c, data = client
        c.post(f"/api/v1/tasks/{data['task_id']}/claim", headers=_hdr(data["token"]), json={})
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/progress",
            headers=_hdr(data["token"]),
            json={"progress_percent": 75},
        )
        assert resp.status_code == 200


class TestGetClaimsEndpoint:
    def test_get_claims_returns_claims(self, client):
        c, data = client
        task_id = data["task_id"]
        # Create a claim via POST
        resp = c.post(
            f"/api/v1/tasks/{task_id}/claim",
            headers=_hdr(data["token"]),
            json={"context_snapshot": "snap1"},
        )
        assert resp.status_code == 201
        claim_id = resp.json()["id"]

        # GET claims
        resp = c.get(f"/api/v1/tasks/{task_id}/claims")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert len(body["items"]) == 1
        item = body["items"][0]
        assert item["id"] == claim_id
        assert item["task_id"] == task_id
        assert item["state"] == "active"
        assert item["context_snapshot"] == "snap1"

    def test_get_claims_empty_when_no_claims(self, client):
        c, data = client
        task_id = data["task_id"]
        resp = c.get(f"/api/v1/tasks/{task_id}/claims")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_get_claims_404_for_nonexistent_task(self, client):
        c, _ = client
        resp = c.get("/api/v1/tasks/nonexistent-id/claims")
        assert resp.status_code == 404


class TestGetHeartbeatsEndpoint:
    def test_get_heartbeats_returns_heartbeats(self, client):
        c, data = client
        task_id = data["task_id"]
        # Create a claim
        c.post(
            f"/api/v1/tasks/{task_id}/claim",
            headers=_hdr(data["token"]),
            json={},
        )
        # Send a heartbeat
        c.post(
            f"/api/v1/tasks/{task_id}/heartbeat",
            headers=_hdr(data["token"]),
            json={
                "progress_percent": 40,
                "current_step": "step1",
                "next_step": "step2",
                "blockers": "none",
                "eta": "2h",
            },
        )

        # GET heartbeats
        resp = c.get(f"/api/v1/tasks/{task_id}/heartbeats")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert len(body["items"]) == 1
        hb = body["items"][0]
        assert hb["progress_percent"] == 40
        assert hb["current_step"] == "step1"
        assert hb["next_step"] == "step2"
        assert hb["blockers"] == "none"
        assert hb["eta"] == "2h"
        assert "created_at" in hb

    def test_get_heartbeats_empty_when_none(self, client):
        c, data = client
        resp = c.get(f"/api/v1/tasks/{data['task_id']}/heartbeats")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_get_heartbeats_404_for_nonexistent_task(self, client):
        c, _ = client
        resp = c.get("/api/v1/tasks/nonexistent-id/heartbeats")
        assert resp.status_code == 404


class TestGetClarificationsEndpoint:
    def test_get_clarifications_returns_items(self, client):
        c, data = client
        task_id = data["task_id"]
        # Create a clarification request directly in DB
        session = _TestSession()
        try:
            cr = ClarificationRequest(
                id=new_id(),
                task_id=task_id,
                author_type="agent",
                author_id=data["agent_id"],
                question="What is the expected format?",
                context="For CSV export",
                blocking=True,
                state="open",
            )
            session.add(cr)
            session.commit()
            cr_id = cr.id
        finally:
            session.close()

        resp = c.get(f"/api/v1/tasks/{task_id}/clarifications")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert len(body["items"]) == 1
        item = body["items"][0]
        assert item["id"] == cr_id
        assert item["task_id"] == task_id
        assert item["question"] == "What is the expected format?"
        assert item["blocking"] is True
        assert item["state"] == "open"

    def test_get_clarifications_empty_when_none(self, client):
        c, data = client
        resp = c.get(f"/api/v1/tasks/{data['task_id']}/clarifications")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_get_clarifications_404_for_nonexistent_task(self, client):
        c, _ = client
        resp = c.get("/api/v1/tasks/nonexistent-id/clarifications")
        assert resp.status_code == 404
