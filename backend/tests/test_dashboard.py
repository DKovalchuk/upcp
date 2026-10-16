"""Tests for dashboard statistics endpoint."""

from datetime import timedelta

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.structure import router as structure_router

# Import all models to ensure all tables are created
from app.audit.models import AuditEvent  # noqa: F401
from app.audit.service import AuditService
from app.delivery.models import Feature, Heartbeat, Task, TaskClaim  # noqa: F401
from app.identity.agents import Agent  # noqa: F401
from app.identity.models import User  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from app.shared.text import new_id, utcnow
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=_test_engine)


def _override_session():
    session = TestSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _test_app() -> FastAPI:
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(structure_router, prefix="/api/v1")
    app.include_router(delivery_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    return app


def test_dashboard_stats_empty_database() -> None:
    """Test dashboard stats with empty database returns zeros and empty arrays."""
    client = TestClient(_test_app())
    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    # Check project count
    assert data["project_count"] == 0

    # Check task counts by status
    assert data["task_counts_by_status"]["backlog"] == 0
    assert data["task_counts_by_status"]["in_progress"] == 0
    assert data["task_counts_by_status"]["review"] == 0
    assert data["task_counts_by_status"]["done"] == 0

    # Check recent projects
    assert data["recent_projects"] == []

    # Check recent activity
    assert data["recent_activity"] == []


def test_dashboard_stats_with_data() -> None:
    """Test dashboard stats with populated database."""
    client = TestClient(_test_app())

    # Create projects
    project1 = client.post("/api/v1/projects", json={"name": "Project 1"}).json()
    project2 = client.post("/api/v1/projects", json={"name": "Project 2"}).json()

    # Create features and tasks for project1
    feature1_resp = client.post(
        f"/api/v1/projects/{project1['id']}/features",
        json={"name": "Feature 1", "slug": "feature-1"},
    )
    if feature1_resp.status_code != 201:
        print("Feature creation failed:", feature1_resp.status_code, feature1_resp.json())
    feature1 = feature1_resp.json()

    # Create tasks with different statuses
    task1_resp = client.post(
        f"/api/v1/features/{feature1['id']}/tasks", json={"title": "Task 1", "status": "backlog"}
    )
    client.post(
        f"/api/v1/features/{feature1['id']}/tasks",
        json={"title": "Task 2", "status": "in_progress"},
    )
    client.post(
        f"/api/v1/features/{feature1['id']}/tasks", json={"title": "Task 3", "status": "review"}
    )
    client.post(
        f"/api/v1/features/{feature1['id']}/tasks", json={"title": "Task 4", "status": "done"}
    )
    client.post(
        f"/api/v1/features/{feature1['id']}/tasks", json={"title": "Task 5", "status": "done"}
    )

    # Create audit events manually
    session = TestSessionLocal()
    audit_service = AuditService(session)
    audit_service.log_event(
        event_type="project.created",
        entity_type="project",
        entity_id=project1["id"],
        actor_type="user",
        actor_id="test-user",
    )
    audit_service.log_event(
        event_type="project.created",
        entity_type="project",
        entity_id=project2["id"],
        actor_type="user",
        actor_id="test-user",
    )
    audit_service.log_event(
        event_type="task.created",
        entity_type="task",
        entity_id=task1_resp.json()["id"],
        actor_type="user",
        actor_id="test-user",
    )
    session.commit()
    session.close()

    # Check dashboard stats
    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    # Check project count
    assert data["project_count"] == 2

    # Check task counts by status
    assert data["task_counts_by_status"]["backlog"] == 1
    assert data["task_counts_by_status"]["in_progress"] == 1
    assert data["task_counts_by_status"]["review"] == 1
    assert data["task_counts_by_status"]["done"] == 2

    # Check recent projects (should be sorted by updated_at desc)
    assert len(data["recent_projects"]) == 2
    assert data["recent_projects"][0]["name"] == "Project 2"
    assert data["recent_projects"][1]["name"] == "Project 1"

    # Check recent activity (audit events)
    assert len(data["recent_activity"]) == 3


def test_dashboard_stats_recent_projects_limit() -> None:
    """Test that recent_projects is limited to 5 items."""
    client = TestClient(_test_app())

    # Create 6 projects
    for i in range(6):
        client.post("/api/v1/projects", json={"name": f"Project {i}"})

    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    # Should only return 5 recent projects
    assert len(data["recent_projects"]) == 5
    assert data["project_count"] == 6


def test_dashboard_stats_recent_activity_limit() -> None:
    """Test that recent_activity is limited to 10 items."""
    client = TestClient(_test_app())

    # Create a project and feature
    project = client.post("/api/v1/projects", json={"name": "Test Project"}).json()
    feature = client.post(
        f"/api/v1/projects/{project['id']}/features",
        json={"name": "Test Feature", "slug": "test-feature"},
    ).json()

    # Create 12 tasks to generate audit events
    for i in range(12):
        client.post(
            f"/api/v1/features/{feature['id']}/tasks",
            json={"title": f"Task {i}", "status": "backlog"},
        )

    # Create 12 audit events manually
    session = TestSessionLocal()
    audit_service = AuditService(session)
    for i in range(12):
        audit_service.log_event(
            event_type=f"task.created.{i}",
            entity_type="task",
            entity_id=f"task-{i}",
            actor_type="user",
            actor_id="test-user",
        )
    session.commit()
    session.close()

    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    # Should only return 10 recent activity items
    assert len(data["recent_activity"]) == 10


# --- Agent Activity endpoint tests ---


def _create_test_data(session, *, stale_heartbeat: bool = False) -> dict:
    """Create Agent, Task, TaskClaim, Heartbeat for agent-activity tests."""
    agent = Agent(id=new_id(), name="test-agent-1")
    session.add(agent)
    session.flush()

    project = Project(id=new_id(), name="P1", slug="p1")
    session.add(project)
    session.flush()

    feature = Feature(id=new_id(), project_id=project.id, name="F1", slug="f1")
    session.add(feature)
    session.flush()

    task = Task(id=new_id(), feature_id=feature.id, title="Test Task")
    session.add(task)
    session.flush()

    hb_time = utcnow() - timedelta(minutes=10) if stale_heartbeat else utcnow()

    claim = TaskClaim(
        id=new_id(),
        task_id=task.id,
        agent_id=agent.id,
        state="active",
        last_heartbeat_at=hb_time,
    )
    session.add(claim)
    session.flush()

    heartbeat = Heartbeat(
        id=new_id(),
        claim_id=claim.id,
        progress_percent=55,
        current_step="writing tests",
        next_step="implementation",
    )
    session.add(heartbeat)
    session.flush()
    session.commit()

    return {
        "agent": agent,
        "task": task,
        "claim": claim,
        "heartbeat": heartbeat,
    }


def test_agent_activity_empty() -> None:
    """Test agent-activity returns empty list when no active claims."""
    client = TestClient(_test_app())
    resp = client.get("/api/v1/dashboard/agent-activity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


def test_agent_activity_with_claim() -> None:
    """Test agent-activity returns agent with task info when claim exists."""
    client = TestClient(_test_app())
    session = TestSessionLocal()
    data = _create_test_data(session)
    # Capture IDs before closing session to avoid DetachedInstanceError
    agent_id = data["agent"].id
    task_id = data["task"].id
    session.close()

    resp = client.get("/api/v1/dashboard/agent-activity")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1

    item = body["items"][0]
    assert item["agent_id"] == agent_id
    assert item["agent_name"] == "test-agent-1"
    assert item["task_id"] == task_id
    assert item["task_title"] == "Test Task"
    assert item["claimed_at"] is not None
    assert item["last_heartbeat_at"] is not None


def test_agent_activity_heartbeat_data() -> None:
    """Test agent-activity returns heartbeat progress and step info."""
    client = TestClient(_test_app())
    session = TestSessionLocal()
    _create_test_data(session)
    session.close()

    resp = client.get("/api/v1/dashboard/agent-activity")
    item = resp.json()["items"][0]
    assert item["progress_percent"] == 55
    assert item["current_step"] == "writing tests"


def test_agent_activity_stale_when_old_heartbeat() -> None:
    """Test is_stale = true when last heartbeat is older than 7 minutes."""
    client = TestClient(_test_app())
    session = TestSessionLocal()
    _create_test_data(session, stale_heartbeat=True)
    session.close()

    resp = client.get("/api/v1/dashboard/agent-activity")
    item = resp.json()["items"][0]
    assert item["is_stale"] is True


def test_agent_activity_fresh_when_recent_heartbeat() -> None:
    """Test is_stale = false when last heartbeat is within 7 minutes."""
    client = TestClient(_test_app())
    session = TestSessionLocal()
    _create_test_data(session, stale_heartbeat=False)
    session.close()

    resp = client.get("/api/v1/dashboard/agent-activity")
    item = resp.json()["items"][0]
    assert item["is_stale"] is False


# ── Sprint 1: New dashboard stats fields ────────────────────


def test_dashboard_stats_new_fields_present() -> None:
    """Test that new fields (done_this_week, blocked_count, claimed_count, health_score) are present."""
    client = TestClient(_test_app())
    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "done_this_week" in data
    assert "blocked_count" in data
    assert "claimed_count" in data
    assert "health_score" in data
    assert "blocked" in data["task_counts_by_status"]


def test_dashboard_stats_empty_db_defaults() -> None:
    """Test new fields default to correct values on empty DB."""
    client = TestClient(_test_app())
    resp = client.get("/api/v1/dashboard/stats")
    data = resp.json()
    assert data["done_this_week"] == 0
    assert data["blocked_count"] == 0
    assert data["claimed_count"] == 0
    assert data["health_score"] == 100
    assert data["task_counts_by_status"]["blocked"] == 0


def test_dashboard_stats_done_this_week_counts_recent() -> None:
    """Test done_this_week counts only tasks completed in last 7 days."""
    client = TestClient(_test_app())
    project = client.post("/api/v1/projects", json={"name": "P1"}).json()
    feature = client.post(
        f"/api/v1/projects/{project['id']}/features",
        json={"name": "F1", "slug": "f1"},
    ).json()

    # Create task and mark done (updated_at will be now)
    client.post(
        f"/api/v1/features/{feature['id']}/tasks",
        json={"title": "Recent done", "status": "done"},
    )

    resp = client.get("/api/v1/dashboard/stats")
    assert resp.json()["done_this_week"] >= 1


def test_dashboard_stats_done_this_week_excludes_old() -> None:
    """Test done_this_week excludes tasks done more than 7 days ago."""
    client = TestClient(_test_app())
    session = TestSessionLocal()

    project = client.post("/api/v1/projects", json={"name": "P1"}).json()
    feature = client.post(
        f"/api/v1/projects/{project['id']}/features",
        json={"name": "F1", "slug": "f1"},
    ).json()
    task = client.post(
        f"/api/v1/features/{feature['id']}/tasks",
        json={"title": "Old done", "status": "done"},
    ).json()

    # Backdate the task's updated_at
    from app.delivery.models import Task

    old_time = utcnow() - timedelta(days=10)
    session.query(Task).filter(Task.id == task["id"]).update({"updated_at": old_time})
    session.commit()
    session.close()

    resp = client.get("/api/v1/dashboard/stats")
    assert resp.json()["done_this_week"] == 0


def test_dashboard_stats_blocked_count() -> None:
    """Test blocked_count counts tasks with blocked status."""
    client = TestClient(_test_app())
    project = client.post("/api/v1/projects", json={"name": "P1"}).json()
    feature = client.post(
        f"/api/v1/projects/{project['id']}/features",
        json={"name": "F1", "slug": "f1"},
    ).json()

    client.post(
        f"/api/v1/features/{feature['id']}/tasks",
        json={"title": "Blocked 1", "status": "blocked"},
    )
    client.post(
        f"/api/v1/features/{feature['id']}/tasks",
        json={"title": "Blocked 2", "status": "blocked"},
    )
    client.post(
        f"/api/v1/features/{feature['id']}/tasks",
        json={"title": "Not blocked", "status": "in_progress"},
    )

    resp = client.get("/api/v1/dashboard/stats")
    assert resp.json()["blocked_count"] == 2
    assert resp.json()["task_counts_by_status"]["blocked"] == 2


def test_dashboard_stats_claimed_count() -> None:
    """Test claimed_count counts tasks with active agent claims."""
    client = TestClient(_test_app())
    session = TestSessionLocal()

    project = client.post("/api/v1/projects", json={"name": "P1"}).json()
    feature = client.post(
        f"/api/v1/projects/{project['id']}/features",
        json={"name": "F1", "slug": "f1"},
    ).json()
    task = client.post(
        f"/api/v1/features/{feature['id']}/tasks",
        json={"title": "Claimed task", "status": "in_progress"},
    ).json()

    # Create agent and claim
    from app.delivery.models import TaskClaim
    from app.identity.agents import Agent

    agent = Agent(id=new_id(), name="test-agent", description="Test Agent")
    session.add(agent)
    claim = TaskClaim(
        id=new_id(),
        task_id=task["id"],
        agent_id=agent.id,
        state="active",
        claimed_at=utcnow(),
    )
    session.add(claim)
    session.commit()
    session.close()

    resp = client.get("/api/v1/dashboard/stats")
    assert resp.json()["claimed_count"] >= 1


def test_dashboard_stats_health_score_range() -> None:
    """Test health_score is between 0 and 100."""
    client = TestClient(_test_app())
    client.post("/api/v1/projects", json={"name": "P1"})
    resp = client.get("/api/v1/dashboard/stats")
    score = resp.json()["health_score"]
    assert 0 <= score <= 100


def test_dashboard_stats_project_id_filter() -> None:
    """Test stats scoped to a specific project."""
    client = TestClient(_test_app())

    p1 = client.post("/api/v1/projects", json={"name": "P1"}).json()
    p2 = client.post("/api/v1/projects", json={"name": "P2"}).json()

    f1 = client.post(
        f"/api/v1/projects/{p1['id']}/features", json={"name": "F1", "slug": "f1"}
    ).json()
    f2 = client.post(
        f"/api/v1/projects/{p2['id']}/features", json={"name": "F2", "slug": "f2"}
    ).json()

    client.post(f"/api/v1/features/{f1['id']}/tasks", json={"title": "T1", "status": "done"})
    client.post(f"/api/v1/features/{f1['id']}/tasks", json={"title": "T2", "status": "done"})
    client.post(f"/api/v1/features/{f2['id']}/tasks", json={"title": "T3", "status": "in_progress"})

    # Global stats
    global_stats = client.get("/api/v1/dashboard/stats").json()
    assert global_stats["task_counts_by_status"]["done"] == 2
    assert global_stats["task_counts_by_status"]["in_progress"] == 1

    # Scoped to P1
    p1_stats = client.get(f"/api/v1/dashboard/stats?project_id={p1['id']}").json()
    assert p1_stats["task_counts_by_status"]["done"] == 2
    assert p1_stats["task_counts_by_status"]["in_progress"] == 0

    # Scoped to P2
    p2_stats = client.get(f"/api/v1/dashboard/stats?project_id={p2['id']}").json()
    assert p2_stats["task_counts_by_status"]["done"] == 0
    assert p2_stats["task_counts_by_status"]["in_progress"] == 1


def test_dashboard_stats_nonexistent_project() -> None:
    """Test stats with nonexistent project_id returns zeros, not error."""
    client = TestClient(_test_app())
    resp = client.get("/api/v1/dashboard/stats?project_id=nonexistent-uuid")
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_counts_by_status"]["done"] == 0
    assert data["done_this_week"] == 0


# ── Attention endpoint project scoping (TASK-0125) ─────────


def test_dashboard_attention_project_id_filter() -> None:
    """Test attention endpoint scoped to a project returns only its items."""
    client = TestClient(_test_app())

    p1 = client.post("/api/v1/projects", json={"name": "P1"}).json()
    p2 = client.post("/api/v1/projects", json={"name": "P2"}).json()
    f1 = client.post(
        f"/api/v1/projects/{p1['id']}/features", json={"name": "F1", "slug": "f1"}
    ).json()
    f2 = client.post(
        f"/api/v1/projects/{p2['id']}/features", json={"name": "F2", "slug": "f2"}
    ).json()
    t1 = client.post(
        f"/api/v1/features/{f1['id']}/tasks", json={"title": "Blocked 1", "status": "blocked"}
    ).json()
    t2 = client.post(
        f"/api/v1/features/{f2['id']}/tasks", json={"title": "Blocked 2", "status": "blocked"}
    ).json()

    # Unscoped: both blocked tasks
    resp = client.get("/api/v1/dashboard/attention")
    assert resp.status_code == 200
    unscoped = resp.json()
    assert {i["task_id"] for i in unscoped["blocked_tasks"]} == {t1["id"], t2["id"]}

    # Scoped to P1: only P1's blocked task, with project_id attached
    resp = client.get(f"/api/v1/dashboard/attention?project_id={p1['id']}")
    assert resp.status_code == 200
    scoped = resp.json()
    assert [i["task_id"] for i in scoped["blocked_tasks"]] == [t1["id"]]
    assert scoped["blocked_tasks"][0]["project_id"] == p1["id"]


def test_dashboard_attention_nonexistent_project() -> None:
    """Test attention endpoint with nonexistent project_id returns empty sections."""
    client = TestClient(_test_app())
    resp = client.get("/api/v1/dashboard/attention?project_id=nonexistent-uuid")
    assert resp.status_code == 200
    data = resp.json()
    assert data["blocked_tasks"] == []
    assert data["needs_review"] == []
    assert data["open_questions"] == []
    assert data["low_health_projects"] == []
