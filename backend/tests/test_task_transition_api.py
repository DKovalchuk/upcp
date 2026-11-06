"""HTTP status for invalid task lifecycle transitions must be 422, not 500.

`validate_transition` (app.delivery.lifecycle) raises `InvalidTransition`,
a plain ``Exception``. Endpoints that did not catch it fell through to the
generic catch-all handler and returned 500 ``{"error": "internal_error"}``
— reproduced on the live dev stack with
``PATCH /api/v1/tasks/{task_id}`` ``{"status": "backlog"}`` on a ``done`` task.

Regression tests for every HTTP surface audited to leak `InvalidTransition`:

- PATCH  /api/v1/tasks/{task_id}                 (delivery router)
- POST   /api/v1/tasks/{task_id}/release         (workflow router)
- POST   /api/v1/tasks/{task_id}/clarifications  (blocking=true)
- POST   /api/v1/clarifications/{id}/answer      (blocking=true)

Precedent: `bulk_update_tasks` already maps invalid transitions to 422.
"""

from __future__ import annotations

import hashlib
import uuid

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
import pytest
from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.task_workflow import router as workflow_router
from app.delivery.models import ClarificationRequest, Feature, Task
from app.identity.agents import Agent, AgentToken
from app.identity.models import User
from app.projects.models import Project
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from app.shared.text import new_id
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _override_session, _test_engine, _TestSession

_RAW_TOKEN = "test-token-trans"


def _make_app(*routers: object) -> FastAPI:
    """Build an app with the global error handlers and the shared test DB."""
    app = FastAPI()
    register_error_handlers(app)
    for router in routers:
        app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    return app


# ── PATCH /api/v1/tasks/{task_id} ─────────────────────────────────


class TestPatchTaskInvalidTransition:
    """PATCH task with a status the lifecycle state machine forbids."""

    def _seed_task(self, status: str) -> tuple[TestClient, str]:
        Base.metadata.drop_all(bind=_test_engine)
        Base.metadata.create_all(bind=_test_engine)
        # raise_server_exceptions=False: the pre-fix behaviour (unhandled
        # InvalidTransition → 500 {"error": "internal_error"}) must be
        # observable as a response, mirroring the live-stack repro.
        client = TestClient(
            _make_app(projects_router, delivery_router), raise_server_exceptions=False
        )
        pid = client.post("/api/v1/projects", json={"name": "P"}).json()["id"]
        fid = client.post(f"/api/v1/projects/{pid}/features", json={"name": "F"}).json()["id"]
        tid = client.post(
            f"/api/v1/features/{fid}/tasks", json={"title": "T", "status": status}
        ).json()["id"]
        return client, tid

    def test_done_to_backlog_returns_422(self) -> None:
        """done → backlog is forbidden: must be 422 with the transition detail."""
        client, tid = self._seed_task("done")
        resp = client.patch(f"/api/v1/tasks/{tid}", json={"status": "backlog"})
        assert resp.status_code == 422
        assert "Cannot transition" in resp.json()["detail"]

    def test_valid_transition_still_succeeds(self) -> None:
        """Sanity: a legal transition (ready → backlog) still returns 200."""
        client, tid = self._seed_task("ready")
        resp = client.patch(f"/api/v1/tasks/{tid}", json={"status": "backlog"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "backlog"


# ── Workflow endpoints (release / clarifications) ──────────────────


def _set_task_status(task_id: str, status: str) -> None:
    session = _TestSession()
    try:
        session.get(Task, task_id).status = status
        session.commit()
    finally:
        session.close()


def _seed_blocking_clarification(task_id: str, agent_id: str) -> str:
    session = _TestSession()
    try:
        cr = ClarificationRequest(
            id=new_id(),
            task_id=task_id,
            author_type="agent",
            author_id=agent_id,
            question="Blocking question?",
            blocking=True,
            state="open",
        )
        session.add(cr)
        session.commit()
        return cr.id
    finally:
        session.close()


@pytest.fixture()
def wf_client():
    """Workflow API client with a task, an agent token, and an active claim.

    Task starts in ``in_progress`` with an active claim held by the agent —
    the state right before a release attempt.
    """
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    client = TestClient(_make_app(workflow_router), raise_server_exceptions=False)
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
        session.flush()
        from app.delivery.models import TaskClaim

        claim = TaskClaim(id=new_id(), task_id=t.id, agent_id=agent.id, state="active")
        session.add(claim)
        session.commit()

        result = {"task_id": t.id, "agent_id": agent.id, "token": f"{_RAW_TOKEN}-{uid}"}
    except Exception:
        session.rollback()
        session.close()
        raise
    session.close()

    yield client, result

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


def _hdr(token: str) -> dict[str, str]:
    return {"X-Agent-Token": token}


class TestReleaseInvalidTransition:
    def test_release_in_progress_task_returns_422(self, wf_client) -> None:
        """Release on a task that left ``claimed`` (here: in_progress) → 422.

        in_progress → backlog is not a valid edge; pre-fix this returned 500.
        """
        c, data = wf_client
        _set_task_status(data["task_id"], "in_progress")
        resp = c.post(f"/api/v1/tasks/{data['task_id']}/release", headers=_hdr(data["token"]))
        assert resp.status_code == 422
        assert "Cannot transition" in resp.json()["detail"]

    def test_release_claimed_task_still_succeeds(self, wf_client) -> None:
        """Sanity: release right after claim (claimed → backlog) still 200."""
        c, data = wf_client
        _set_task_status(data["task_id"], "claimed")
        resp = c.post(f"/api/v1/tasks/{data['task_id']}/release", headers=_hdr(data["token"]))
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


class TestBlockingClarificationInvalidTransition:
    def test_blocking_clarification_on_claimed_task_returns_422(self, wf_client) -> None:
        """Blocking clarification while task is ``claimed`` → 422.

        claimed → needs_clarification is not a valid edge (an agent claiming
        a task and immediately asking a blocking question hit 500 pre-fix).
        """
        c, data = wf_client
        _set_task_status(data["task_id"], "claimed")
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/clarifications",
            headers=_hdr(data["token"]),
            json={"question": "Which format?", "blocking": True},
        )
        assert resp.status_code == 422
        assert "Cannot transition" in resp.json()["detail"]

    def test_non_blocking_clarification_still_succeeds(self, wf_client) -> None:
        """Sanity: non-blocking clarification performs no transition → 201."""
        c, data = wf_client
        _set_task_status(data["task_id"], "claimed")
        resp = c.post(
            f"/api/v1/tasks/{data['task_id']}/clarifications",
            headers=_hdr(data["token"]),
            json={"question": "Which format?", "blocking": False},
        )
        assert resp.status_code == 201


class TestAnswerClarificationInvalidTransition:
    def test_answer_blocking_clarification_invalid_task_status_returns_422(self, wf_client) -> None:
        """Answering a blocking clarification with the task off-edge → 422.

        ready → in_progress is not a valid edge; pre-fix this returned 500.
        """
        c, data = wf_client
        _set_task_status(data["task_id"], "ready")
        cr_id = _seed_blocking_clarification(data["task_id"], data["agent_id"])
        resp = c.post(
            f"/api/v1/clarifications/{cr_id}/answer",
            headers=_hdr(data["token"]),
            json={"answer": "Use JSON"},
        )
        assert resp.status_code == 422
        assert "Cannot transition" in resp.json()["detail"]

    def test_answer_blocking_clarification_valid_status_still_succeeds(self, wf_client) -> None:
        """Sanity: needs_clarification → in_progress still returns 200."""
        c, data = wf_client
        _set_task_status(data["task_id"], "needs_clarification")
        cr_id = _seed_blocking_clarification(data["task_id"], data["agent_id"])
        resp = c.post(
            f"/api/v1/clarifications/{cr_id}/answer",
            headers=_hdr(data["token"]),
            json={"answer": "Use JSON"},
        )
        assert resp.status_code == 200
        assert resp.json()["state"] == "answered"
