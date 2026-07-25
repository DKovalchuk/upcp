"""Tests for dashboard statistics endpoint."""

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.structure import router as structure_router

# Import all models to ensure all tables are created
from app.audit.models import AuditEvent  # noqa: F401
from app.audit.service import AuditService
from app.delivery.models import Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
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
