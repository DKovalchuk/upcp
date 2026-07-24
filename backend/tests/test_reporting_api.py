from app.api.v1.projects import router as projects_router
from app.api.v1.reporting import router
from app.api.v1.structure import router as structure_router

# Import all models to ensure all tables are created
from app.reporting.models import Report  # noqa: F401
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
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    return app


def test_generate_daily_report() -> None:
    """Test generating a daily report for a project."""
    client = TestClient(_test_app())
    
    # First create a project
    project_resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    print("Project response:", project_resp.status_code, project_resp.json())
    project_id = project_resp.json()["id"]
    
    # Generate daily report
    resp = client.post(f"/api/v1/projects/{project_id}/reports/daily")
    assert resp.status_code == 201
    data = resp.json()
    assert data["report_type"] == "daily"
    assert data["project_id"] == project_id
    assert "content" in data
    assert "task_counts" in data["content"]
    assert "recent_changes" in data["content"]
    assert "blockers" in data["content"]


def test_generate_daily_report_project_not_found() -> None:
    """Test generating daily report for non-existent project."""
    client = TestClient(_test_app())
    resp = client.post("/api/v1/projects/nonexistent/reports/daily")
    assert resp.status_code == 404


def test_get_report() -> None:
    """Test getting a report by ID."""
    client = TestClient(_test_app())
    
    # Create a project
    project_resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    project_id = project_resp.json()["id"]
    
    # Generate daily report
    report_resp = client.post(f"/api/v1/projects/{project_id}/reports/daily")
    report_id = report_resp.json()["id"]
    
    # Get report
    resp = client.get(f"/api/v1/reports/{report_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == report_id
    assert data["project_id"] == project_id


def test_get_report_not_found() -> None:
    """Test getting non-existent report."""
    client = TestClient(_test_app())
    resp = client.get("/api/v1/reports/nonexistent")
    assert resp.status_code == 404


def test_export_report_markdown() -> None:
    """Test exporting report as markdown."""
    client = TestClient(_test_app())
    
    # Create a project
    project_resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    project_id = project_resp.json()["id"]
    
    # Generate daily report
    report_resp = client.post(f"/api/v1/projects/{project_id}/reports/daily")
    report_id = report_resp.json()["id"]
    
    # Export as markdown
    resp = client.get(f"/api/v1/reports/{report_id}/markdown")
    assert resp.status_code == 200
    data = resp.json()
    assert "markdown" in data
    assert "# Daily Report" in data["markdown"]
    assert "Test Project" in data["markdown"]


def test_export_report_markdown_not_found() -> None:
    """Test exporting non-existent report as markdown."""
    client = TestClient(_test_app())
    resp = client.get("/api/v1/reports/nonexistent/markdown")
    assert resp.status_code == 404


def test_summarize_report_placeholder() -> None:
    """Test summarize endpoint returns placeholder error."""
    client = TestClient(_test_app())
    
    # Create a project
    project_resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    project_id = project_resp.json()["id"]
    
    # Generate daily report
    report_resp = client.post(f"/api/v1/projects/{project_id}/reports/daily")
    report_id = report_resp.json()["id"]
    
    # Try to summarize
    resp = client.post(f"/api/v1/reports/{report_id}/summarize")
    assert resp.status_code == 422
    # The error could be about LLM not enabled or unknown provider
    assert "LLM" in resp.json()["detail"] or "provider" in resp.json()["detail"]


def test_list_project_reports() -> None:
    """Test listing reports for a project."""
    client = TestClient(_test_app())
    
    # Create a project
    project_resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    project_id = project_resp.json()["id"]
    
    # Generate multiple reports
    for _ in range(3):
        client.post(f"/api/v1/projects/{project_id}/reports/daily")
    
    # List reports
    resp = client.get(f"/api/v1/projects/{project_id}/reports")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert all(r["project_id"] == project_id for r in data["items"])