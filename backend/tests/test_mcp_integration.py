"""Integration tests for MCP tools/calling with real data."""
import json

import pytest
from app.api.v1.audit import router as audit_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.structure import router as structure_router
from app.audit.models import AuditEvent  # noqa: F401
from app.delivery.models import Feature, Subtask, Task  # noqa: F401
from app.mcp.server import create_mcp_router
from app.projects.models import Project  # noqa: F401
from app.quality.models import AcceptanceCriterion, DoDItem  # noqa: F401
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from app.structure.models import Component, Module  # noqa: F401
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
    app.include_router(quality_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")
    mcp_router = create_mcp_router()
    app.include_router(mcp_router, prefix="/mcp")
    # Override get_session for both API and MCP routes
    app.dependency_overrides[get_session] = _override_session
    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_test_app())


def _create_test_data(client: TestClient) -> dict:
    """Create a full set of test data and return IDs."""
    # Project
    p = client.post("/api/v1/projects", json={"name": "MCP Test", "description": "Integration test"})
    project = p.json()

    # Component
    c = client.post(f"/api/v1/projects/{project['id']}/components", json={"name": "Backend", "slug": "backend"})
    component = c.json()

    # Module
    m = client.post(f"/api/v1/components/{component['id']}/modules", json={"name": "API", "slug": "api"})
    module = m.json()

    # Feature
    f = client.post(f"/api/v1/projects/{project['id']}/features", json={"name": "Auth", "slug": "auth"})
    feature = f.json()

    # Tasks
    tasks = []
    for i, (status, priority) in enumerate([("backlog", 0), ("in_progress", 1), ("done", 2)]):
        t = client.post(f"/api/v1/features/{feature['id']}/tasks", json={
            "title": f"Task {i+1}", "status": status, "priority": priority,
            "component_id": component["id"], "module_id": module["id"],
        })
        tasks.append(t.json())

    # Subtasks
    st = client.post(f"/api/v1/tasks/{tasks[0]['id']}/subtasks", json={"title": "Subtask 1"})
    subtask = st.json()

    # Acceptance Criterion
    ac = client.post(f"/api/v1/tasks/{tasks[0]['id']}/acceptance-criteria", json={"description": "Works correctly"})
    acceptance_criterion = ac.json()

    # DoD Item
    dod = client.post(f"/api/v1/tasks/{tasks[0]['id']}/dod-items", json={"name": "Code reviewed"})
    dod_item = dod.json()

    return {
        "project": project,
        "component": component,
        "module": module,
        "feature": feature,
        "tasks": tasks,
        "subtask": subtask,
        "ac": acceptance_criterion,
        "dod": dod_item,
    }


# ============================================================
# MCP Protocol Tests
# ============================================================

class TestMCPProtocol:
    def test_health(self, client: TestClient) -> None:
        r = client.get("/mcp/")
        assert r.status_code == 200
        assert r.json() == {"status": "ok", "service": "mcp-server"}

    def test_initialize(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}
        })
        assert r.status_code == 200
        data = r.json()
        assert data["result"]["protocolVersion"] == "2024-11-05"
        assert data["result"]["serverInfo"]["name"] == "upcp-mcp-server"

    def test_tools_list(self, client: TestClient) -> None:
        r = client.get("/mcp/tools")
        assert r.status_code == 200
        tools = r.json()["tools"]
        names = [t["name"] for t in tools]
        # Read tools
        assert "project_list" in names
        assert "project_get" in names
        assert "task_list" in names
        assert "task_get" in names
        assert "feature_list" in names
        assert "feature_get" in names
        # Write tools
        assert "project_create" in names
        assert "project_update" in names
        assert "feature_create" in names
        assert "task_create" in names

    def test_resources_list(self, client: TestClient) -> None:
        r = client.get("/mcp/resources")
        assert r.status_code == 200
        resources = r.json()["resources"]
        assert len(resources) >= 1
        assert resources[0]["uri"] == "context_pack://project"

    def test_unknown_method(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 2, "method": "unknown_method", "params": {}
        })
        data = r.json()
        assert data["error"]["code"] == -32601

    def test_unknown_tool(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "nonexistent", "arguments": {}}
        })
        data = r.json()
        # Unknown tool raises ValueError, caught by outer handler → JSON-RPC error
        assert data["error"] is not None
        assert "Unknown tool" in data["error"]["message"]


# ============================================================
# MCP Tools/calling Tests — Project
# ============================================================

class TestMCPProjectTools:
    def test_project_list_empty(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 10, "method": "tools/call",
            "params": {"name": "project_list", "arguments": {"offset": 0, "limit": 10}}
        })
        data = r.json()
        assert data["result"]["is_error"] is not True
        result = json.loads(data["result"]["content"][0]["text"])
        assert result["items"] == []
        assert result["total"] == 0

    def test_project_list_with_data(self, client: TestClient) -> None:
        _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 11, "method": "tools/call",
            "params": {"name": "project_list", "arguments": {"offset": 0, "limit": 10}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["total"] == 1
        assert result["items"][0]["name"] == "MCP Test"
        assert result["items"][0]["slug"] == "mcp-test"

    def test_project_get(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 12, "method": "tools/call",
            "params": {"name": "project_get", "arguments": {"project_id": data["project"]["id"]}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["name"] == "MCP Test"
        assert result["status"] == "active"

    def test_project_get_not_found(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 13, "method": "tools/call",
            "params": {"name": "project_get", "arguments": {"project_id": "nonexistent"}}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "not found" in data["result"]["content"][0]["text"]

    def test_project_get_missing_param(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 14, "method": "tools/call",
            "params": {"name": "project_get", "arguments": {}}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "required" in data["result"]["content"][0]["text"]


# ============================================================
# MCP Tools/calling Tests — Feature
# ============================================================

class TestMCPFeatureTools:
    def test_feature_list(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 20, "method": "tools/call",
            "params": {"name": "feature_list", "arguments": {"project_id": data["project"]["id"]}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["total"] == 1
        assert result["items"][0]["name"] == "Auth"

    def test_feature_get(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 21, "method": "tools/call",
            "params": {"name": "feature_get", "arguments": {"feature_id": data["feature"]["id"]}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["name"] == "Auth"
        assert result["project_id"] == data["project"]["id"]


# ============================================================
# MCP Tools/calling Tests — Task
# ============================================================

class TestMCPTaskTools:
    def test_task_list_by_project(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 30, "method": "tools/call",
            "params": {"name": "task_list", "arguments": {"project_id": data["project"]["id"]}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["total"] == 3
        titles = [t["title"] for t in result["items"]]
        assert "Task 1" in titles
        assert "Task 2" in titles
        assert "Task 3" in titles

    def test_task_get(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 31, "method": "tools/call",
            "params": {"name": "task_get", "arguments": {"task_id": data["tasks"][0]["id"]}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["title"] == "Task 1"
        assert result["status"] == "backlog"
        assert result["priority"] == 0

    def test_task_list_empty_project(self, client: TestClient) -> None:
        p = client.post("/api/v1/projects", json={"name": "Empty"})
        project = p.json()
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 32, "method": "tools/call",
            "params": {"name": "task_list", "arguments": {"project_id": project["id"]}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["total"] == 0
        assert result["items"] == []


# ============================================================
# MCP Tools/calling Tests — Pagination
# ============================================================

class TestMCPPagination:
    def test_project_list_pagination(self, client: TestClient) -> None:
        # Create 5 projects
        for i in range(5):
            client.post("/api/v1/projects", json={"name": f"Project {i}"})

        # Get page 1
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 40, "method": "tools/call",
            "params": {"name": "project_list", "arguments": {"offset": 0, "limit": 2}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["total"] == 5
        assert len(result["items"]) == 2
        assert result["offset"] == 0
        assert result["limit"] == 2

        # Get page 2
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 41, "method": "tools/call",
            "params": {"name": "project_list", "arguments": {"offset": 2, "limit": 2}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert len(result["items"]) == 2
        assert result["offset"] == 2

    def test_limit_clamped_to_100(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 42, "method": "tools/call",
            "params": {"name": "project_list", "arguments": {"offset": 0, "limit": 999}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["limit"] == 100

    def test_negative_offset_clamped(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 43, "method": "tools/call",
            "params": {"name": "project_list", "arguments": {"offset": -5, "limit": 10}}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["offset"] == 0


# ============================================================
# MCP Tools/calling Tests — Write: project_create
# ============================================================

class TestMCPProjectCreate:
    def test_project_create(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 50, "method": "tools/call",
            "params": {"name": "project_create", "arguments": {
                "name": "New Project", "description": "Created via MCP"
            }}
        })
        assert r.status_code == 200
        data = r.json()
        assert data["result"]["is_error"] is not True
        result = json.loads(data["result"]["content"][0]["text"])
        assert result["name"] == "New Project"
        assert result["slug"] == "new-project"
        assert result["description"] == "Created via MCP"
        assert result["status"] == "active"
        assert "id" in result

    def test_project_create_with_custom_slug(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 51, "method": "tools/call",
            "params": {"name": "project_create", "arguments": {
                "name": "My Project", "slug": "custom-slug"
            }}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["slug"] == "custom-slug"

    def test_project_create_duplicate_slug(self, client: TestClient) -> None:
        client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 52, "method": "tools/call",
            "params": {"name": "project_create", "arguments": {"name": "First"}}
        })
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 53, "method": "tools/call",
            "params": {"name": "project_create", "arguments": {"name": "First"}}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "already exists" in data["result"]["content"][0]["text"]

    def test_project_create_missing_name(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 54, "method": "tools/call",
            "params": {"name": "project_create", "arguments": {"description": "no name"}}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "required" in data["result"]["content"][0]["text"]

    def test_project_create_persists(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 55, "method": "tools/call",
            "params": {"name": "project_create", "arguments": {"name": "Persist Me"}}
        })
        created = json.loads(r.json()["result"]["content"][0]["text"])
        # Verify it shows up in list
        r2 = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 56, "method": "tools/call",
            "params": {"name": "project_get", "arguments": {"project_id": created["id"]}}
        })
        fetched = json.loads(r2.json()["result"]["content"][0]["text"])
        assert fetched["name"] == "Persist Me"


# ============================================================
# MCP Tools/calling Tests — Write: project_update
# ============================================================

class TestMCPProjectUpdate:
    def test_project_update_name(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 60, "method": "tools/call",
            "params": {"name": "project_update", "arguments": {
                "project_id": data["project"]["id"], "name": "Updated Name"
            }}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["name"] == "Updated Name"
        assert result["id"] == data["project"]["id"]

    def test_project_update_status(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 61, "method": "tools/call",
            "params": {"name": "project_update", "arguments": {
                "project_id": data["project"]["id"], "status": "archived"
            }}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["status"] == "archived"

    def test_project_update_description(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 62, "method": "tools/call",
            "params": {"name": "project_update", "arguments": {
                "project_id": data["project"]["id"], "description": "New desc"
            }}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["description"] == "New desc"

    def test_project_update_missing_project_id(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 63, "method": "tools/call",
            "params": {"name": "project_update", "arguments": {"name": "No ID"}}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "required" in data["result"]["content"][0]["text"]

    def test_project_update_not_found(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 64, "method": "tools/call",
            "params": {"name": "project_update", "arguments": {
                "project_id": "nonexistent", "name": "X"
            }}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "not found" in data["result"]["content"][0]["text"]

    def test_project_update_no_fields(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 65, "method": "tools/call",
            "params": {"name": "project_update", "arguments": {
                "project_id": data["project"]["id"]
            }}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        # Name unchanged
        assert result["name"] == "MCP Test"


# ============================================================
# MCP Tools/calling Tests — Write: feature_create
# ============================================================

class TestMCPFeatureCreate:
    def test_feature_create(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 70, "method": "tools/call",
            "params": {"name": "feature_create", "arguments": {
                "project_id": data["project"]["id"], "name": "New Feature",
                "description": "Feature via MCP"
            }}
        })
        assert r.status_code == 200
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["name"] == "New Feature"
        assert result["slug"] == "new-feature"
        assert result["description"] == "Feature via MCP"
        assert result["project_id"] == data["project"]["id"]
        assert result["status"] == "backlog"

    def test_feature_create_with_custom_slug(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 71, "method": "tools/call",
            "params": {"name": "feature_create", "arguments": {
                "project_id": data["project"]["id"], "name": "Feat",
                "slug": "feat-custom"
            }}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["slug"] == "feat-custom"

    def test_feature_create_duplicate_slug(self, client: TestClient) -> None:
        data = _create_test_data(client)
        # "auth" slug already exists from _create_test_data
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 72, "method": "tools/call",
            "params": {"name": "feature_create", "arguments": {
                "project_id": data["project"]["id"], "name": "Auth"
            }}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "already exists" in data["result"]["content"][0]["text"]

    def test_feature_create_missing_project_id(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 73, "method": "tools/call",
            "params": {"name": "feature_create", "arguments": {"name": "Orphan"}}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "required" in data["result"]["content"][0]["text"]

    def test_feature_create_missing_name(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 74, "method": "tools/call",
            "params": {"name": "feature_create", "arguments": {
                "project_id": data["project"]["id"]
            }}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "required" in data["result"]["content"][0]["text"]

    def test_feature_create_persists(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 75, "method": "tools/call",
            "params": {"name": "feature_create", "arguments": {
                "project_id": data["project"]["id"], "name": "Persist Feature"
            }}
        })
        created = json.loads(r.json()["result"]["content"][0]["text"])
        r2 = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 76, "method": "tools/call",
            "params": {"name": "feature_get", "arguments": {"feature_id": created["id"]}}
        })
        fetched = json.loads(r2.json()["result"]["content"][0]["text"])
        assert fetched["name"] == "Persist Feature"


# ============================================================
# MCP Tools/calling Tests — Write: task_create
# ============================================================

class TestMCPTaskCreate:
    def test_task_create(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 80, "method": "tools/call",
            "params": {"name": "task_create", "arguments": {
                "feature_id": data["feature"]["id"], "title": "New Task",
                "description": "Task via MCP"
            }}
        })
        assert r.status_code == 200
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["title"] == "New Task"
        assert result["description"] == "Task via MCP"
        assert result["feature_id"] == data["feature"]["id"]
        assert result["status"] == "backlog"
        assert result["priority"] == 0

    def test_task_create_with_priority(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 81, "method": "tools/call",
            "params": {"name": "task_create", "arguments": {
                "feature_id": data["feature"]["id"], "title": "High Priority",
                "priority": 3, "status": "in_progress"
            }}
        })
        result = json.loads(r.json()["result"]["content"][0]["text"])
        assert result["priority"] == 3
        assert result["status"] == "in_progress"

    def test_task_create_missing_feature_id(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 82, "method": "tools/call",
            "params": {"name": "task_create", "arguments": {"title": "Orphan"}}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "required" in data["result"]["content"][0]["text"]

    def test_task_create_missing_title(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 83, "method": "tools/call",
            "params": {"name": "task_create", "arguments": {
                "feature_id": data["feature"]["id"]
            }}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "required" in data["result"]["content"][0]["text"]

    def test_task_create_persists(self, client: TestClient) -> None:
        data = _create_test_data(client)
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 84, "method": "tools/call",
            "params": {"name": "task_create", "arguments": {
                "feature_id": data["feature"]["id"], "title": "Persist Task"
            }}
        })
        created = json.loads(r.json()["result"]["content"][0]["text"])
        r2 = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 85, "method": "tools/call",
            "params": {"name": "task_get", "arguments": {"task_id": created["id"]}}
        })
        fetched = json.loads(r2.json()["result"]["content"][0]["text"])
        assert fetched["title"] == "Persist Task"

    def test_task_create_feature_not_found(self, client: TestClient) -> None:
        r = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 86, "method": "tools/call",
            "params": {"name": "task_create", "arguments": {
                "feature_id": "nonexistent", "title": "Ghost Task"
            }}
        })
        data = r.json()
        assert data["result"]["is_error"] is True
        assert "not found" in data["result"]["content"][0]["text"]
