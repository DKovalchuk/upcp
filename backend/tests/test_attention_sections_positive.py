"""Positive-path tests for the remaining attention sections — TASK-0083 AC «Tests for each section».

Sections ``stale_claims``, ``rejected_tasks``, ``agent_verdicts_waiting`` and
``low_health_projects`` were previously only asserted EMPTY (empty-DB cases in
``test_attention_dashboard.py`` / ``test_dashboard.py``). These tests seed the
minimum domain rows that make each section non-empty and assert the section
item shape via HTTP ``GET /api/v1/dashboard/attention``.

Seed style follows ``test_dashboard_matrix_ab.py``: shared conftest helpers
(``make_test_app``, ``_TestSession``) — no local engine or local ``_db``
fixture (see ``test_db_fixture_contract.py``).
"""

from datetime import timedelta

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.structure import router as structure_router
from app.delivery.models import Feature, Task, TaskClaim
from app.identity.agents import Agent
from app.projects.models import Project
from app.quality.models import ReviewRound
from app.shared.text import new_id, utcnow
from fastapi.testclient import TestClient

from tests.conftest import _TestSession, make_test_app

ATTENTION_URL = "/api/v1/dashboard/attention"


def _client() -> TestClient:
    """Fresh app with the routes the attention seeding endpoints need."""
    return TestClient(
        make_test_app(projects_router, structure_router, delivery_router, dashboard_router)
    )


def _seed_task(session) -> tuple[Project, Feature, Task]:
    """Seed project → feature → task, flushing parents first (FK contract)."""
    project = Project(id=new_id(), name="Attention P", slug=f"attn-{new_id()[:8]}")
    session.add(project)
    session.flush()
    feature = Feature(id=new_id(), project_id=project.id, name="AF", slug=f"af-{new_id()[:8]}")
    session.add(feature)
    session.flush()
    task = Task(id=new_id(), feature_id=feature.id, title="Attention task", status="in_progress")
    session.add(task)
    session.flush()
    return project, feature, task


def _attention(client: TestClient) -> dict[str, list[dict[str, object]]]:
    resp = client.get(ATTENTION_URL)
    assert resp.status_code == 200
    return resp.json()


# ── stale_claims ────────────────────────────────────────────────


def test_stale_claims_section_positive() -> None:
    """Active claim whose heartbeat is older than 7 minutes appears in stale_claims."""
    client = _client()
    session = _TestSession()
    try:
        project, _feature, task = _seed_task(session)
        agent = Agent(id=new_id(), name=f"stale-agent-{new_id()[:8]}")
        session.add(agent)
        session.flush()
        session.add(
            TaskClaim(
                id=new_id(),
                task_id=task.id,
                agent_id=agent.id,
                state="active",
                claimed_at=utcnow(),
                last_heartbeat_at=utcnow() - timedelta(minutes=15),
            )
        )
        session.commit()
        task_id, agent_id, project_id = task.id, agent.id, project.id
    finally:
        session.close()

    items = _attention(client)["stale_claims"]
    assert len(items) == 1
    item = items[0]
    assert item["task_id"] == task_id
    assert item["agent_id"] == agent_id
    assert item["project_id"] == project_id
    assert item["last_heartbeat"] is not None
    assert item["claimed_at"] is not None


def test_fresh_heartbeat_claim_is_not_stale() -> None:
    """Boundary: a claim heartbeated within the 7-minute window is NOT stale."""
    client = _client()
    session = _TestSession()
    try:
        _project, _feature, task = _seed_task(session)
        agent = Agent(id=new_id(), name=f"fresh-agent-{new_id()[:8]}")
        session.add(agent)
        session.flush()
        session.add(
            TaskClaim(
                id=new_id(),
                task_id=task.id,
                agent_id=agent.id,
                state="active",
                claimed_at=utcnow(),
                last_heartbeat_at=utcnow() - timedelta(minutes=1),
            )
        )
        session.commit()
    finally:
        session.close()

    assert _attention(client)["stale_claims"] == []


# ── rejected_tasks ──────────────────────────────────────────────


def test_rejected_tasks_section_positive() -> None:
    """Completed review round with a reject verdict appears in rejected_tasks."""
    client = _client()
    session = _TestSession()
    try:
        project, _feature, task = _seed_task(session)
        rr = ReviewRound(
            id=new_id(),
            task_id=task.id,
            requested_by_type="agent",
            requested_by_id="req-agent",
            reviewer_type="human",
            reviewer_id="rev-user",
            state="completed",
            verdict="reject",
            summary="Does not match the spec",
            completed_at=utcnow(),
        )
        session.add(rr)
        session.flush()
        session.commit()
        task_id, round_id, project_id = task.id, rr.id, project.id
    finally:
        session.close()

    data = _attention(client)
    items = data["rejected_tasks"]
    assert len(items) == 1
    item = items[0]
    assert item["task_id"] == task_id
    assert item["round_id"] == round_id
    assert item["summary"] == "Does not match the spec"
    assert item["completed_at"] is not None
    assert item["project_id"] == project_id
    # human-requested, human-reviewed round must not leak into the agent-verdict section
    assert data["agent_verdicts_waiting"] == []


# ── agent_verdicts_waiting ──────────────────────────────────────


def test_agent_verdicts_waiting_section_positive() -> None:
    """Completed agent verdict awaiting human confirmation appears in agent_verdicts_waiting."""
    client = _client()
    session = _TestSession()
    try:
        project, _feature, task = _seed_task(session)
        rr = ReviewRound(
            id=new_id(),
            task_id=task.id,
            requested_by_type="human",
            requested_by_id="rev-user",
            reviewer_type="agent",
            reviewer_id="rev-agent",
            state="completed",
            verdict="approve",
            confidence=91,
            summary="Looks good",
            completed_at=utcnow(),
        )
        session.add(rr)
        session.flush()
        session.commit()
        task_id, round_id, project_id = task.id, rr.id, project.id
    finally:
        session.close()

    data = _attention(client)
    items = data["agent_verdicts_waiting"]
    assert len(items) == 1
    item = items[0]
    assert item["task_id"] == task_id
    assert item["round_id"] == round_id
    assert item["verdict"] == "approve"
    assert item["confidence"] == 91
    assert item["project_id"] == project_id
    # an approving round is not a rejection
    assert data["rejected_tasks"] == []


# ── low_health_projects ─────────────────────────────────────────


def test_low_health_projects_section_positive() -> None:
    """Project whose tasks push the score below 70 appears in low_health_projects."""
    client = _client()
    project = client.post("/api/v1/projects", json={"name": "Low Health"}).json()
    feature = client.post(
        f"/api/v1/projects/{project['id']}/features",
        json={"name": "LF", "slug": f"lf-{new_id()[:8]}"},
    ).json()
    for i in range(3):
        resp = client.post(
            f"/api/v1/features/{feature['id']}/tasks",
            json={"title": f"Blocked {i}", "status": "blocked"},
        )
        assert resp.status_code == 201

    items = _attention(client)["low_health_projects"]
    assert len(items) == 1
    item = items[0]
    assert item["project_id"] == project["id"]
    assert item["name"] == "Low Health"
    # 100 - 3 blocked * 15 = 55 < HEALTH_LOW_THRESHOLD (70)
    assert item["score"] < 70
    assert item["top_issue"] == "blocked tasks"
