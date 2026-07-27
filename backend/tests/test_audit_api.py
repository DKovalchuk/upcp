from app.api.v1.audit import router as audit_router
from app.api.v1.projects import router as projects_router
from app.api.v1.structure import router as structure_router

# Import all models to ensure all tables are created
from app.audit.models import AuditEvent  # noqa: F401
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
    app.include_router(audit_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    return app


def test_list_audit_events_empty() -> None:
    """Test listing audit events for a project with no events."""
    client = TestClient(_test_app())
    resp = client.get("/api/v1/projects/nonexistent/audit-events")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["offset"] == 0
    assert data["limit"] == 20


def test_list_audit_events_with_events() -> None:
    """Test listing audit events for a project with events."""
    client = TestClient(_test_app())
    project_resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    project_id = project_resp.json()["id"]
    session = TestSessionLocal()
    from app.audit.service import AuditService

    service = AuditService(session)
    service.log_event(
        event_type="project.created",
        entity_type="project",
        entity_id=project_id,
        actor_type="user",
        actor_id="user-1",
    )
    service.log_event(
        event_type="task.done",
        entity_type="task",
        entity_id=project_id,
        actor_type="agent",
        actor_id="agent-1",
    )
    session.commit()
    session.close()
    resp = client.get(f"/api/v1/projects/{project_id}/audit-events")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    event = data["items"][0]
    assert "id" in event
    assert "timestamp" in event
    assert "event_type" in event
    assert "entity_type" in event
    assert "entity_id" in event
    assert "actor_type" in event
    assert "actor_id" in event
    assert "payload" in event
    assert "note" in event
    assert data["items"][0]["timestamp"] >= data["items"][1]["timestamp"]


def test_list_audit_events_filter_event_type() -> None:
    """Test filtering audit events by event_type."""
    client = TestClient(_test_app())
    project_resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    project_id = project_resp.json()["id"]
    session = TestSessionLocal()
    from app.audit.service import AuditService

    service = AuditService(session)
    service.log_event(
        event_type="project.created",
        entity_type="project",
        entity_id=project_id,
        actor_type="user",
        actor_id="user-1",
    )
    service.log_event(
        event_type="task.done",
        entity_type="task",
        entity_id=project_id,
        actor_type="agent",
        actor_id="agent-1",
    )
    session.commit()
    session.close()
    resp = client.get(
        f"/api/v1/projects/{project_id}/audit-events",
        params={"event_type": "project.created"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["event_type"] == "project.created"


def test_list_audit_events_filter_entity_type() -> None:
    """Test filtering audit events by entity_type."""
    client = TestClient(_test_app())
    project_resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    project_id = project_resp.json()["id"]
    session = TestSessionLocal()
    from app.audit.service import AuditService

    service = AuditService(session)
    service.log_event(
        event_type="project.created",
        entity_type="project",
        entity_id=project_id,
        actor_type="user",
        actor_id="user-1",
    )
    service.log_event(
        event_type="task.done",
        entity_type="task",
        entity_id=project_id,
        actor_type="agent",
        actor_id="agent-1",
    )
    session.commit()
    session.close()
    resp = client.get(
        f"/api/v1/projects/{project_id}/audit-events",
        params={"entity_type": "task"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["entity_type"] == "task"


def test_list_audit_events_pagination() -> None:
    """Test pagination of audit events."""
    client = TestClient(_test_app())
    project_resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    project_id = project_resp.json()["id"]
    session = TestSessionLocal()
    from app.audit.service import AuditService

    service = AuditService(session)
    for i in range(5):
        service.log_event(
            event_type=f"event{i}",
            entity_type="entity",
            entity_id=project_id,
            actor_type="user",
            actor_id="user-1",
        )
    session.commit()
    session.close()
    resp1 = client.get(
        f"/api/v1/projects/{project_id}/audit-events",
        params={"offset": 0, "limit": 2},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["total"] == 5
    assert len(data1["items"]) == 2
    assert data1["offset"] == 0
    assert data1["limit"] == 2
    resp2 = client.get(
        f"/api/v1/projects/{project_id}/audit-events",
        params={"offset": 2, "limit": 2},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total"] == 5
    assert len(data2["items"]) == 2
    ids1 = {item["id"] for item in data1["items"]}
    ids2 = {item["id"] for item in data2["items"]}
    assert ids1.isdisjoint(ids2)
