"""Tests for MCP tools."""

import pytest
from app.mcp.server import create_mcp_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    router = create_mcp_router()
    app.include_router(router, prefix="/mcp")
    return TestClient(app)


class TestMCPTools:
    def test_project_list_tool_exists(self, client: TestClient) -> None:
        response = client.get("/mcp/tools/project_list")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "project_list"

    def test_project_get_tool_exists(self, client: TestClient) -> None:
        response = client.get("/mcp/tools/project_get")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "project_get"

    def test_task_list_tool_exists(self, client: TestClient) -> None:
        response = client.get("/mcp/tools/task_list")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "task_list"

    def test_task_get_tool_exists(self, client: TestClient) -> None:
        response = client.get("/mcp/tools/task_get")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "task_get"

    def test_feature_list_tool_exists(self, client: TestClient) -> None:
        response = client.get("/mcp/tools/feature_list")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "feature_list"

    def test_feature_get_tool_exists(self, client: TestClient) -> None:
        response = client.get("/mcp/tools/feature_get")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "feature_get"


class TestMCPToolExecution:
    def test_project_list_returns_json(self, client: TestClient) -> None:
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "project_list",
                    "arguments": {"offset": 0, "limit": 10},
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "content" in data["result"]

    def test_project_get_with_invalid_id(self, client: TestClient) -> None:
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "project_get",
                    "arguments": {"project_id": "invalid-id"},
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        # Should return error content
        assert data["result"]["is_error"] is True
