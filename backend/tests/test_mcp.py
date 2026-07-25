"""Tests for MCP server."""

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


class TestMCPHealth:
    def test_mcp_endpoint_returns_200(self, client: TestClient) -> None:
        response = client.get("/mcp")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"


class TestMCPTools:
    def test_list_tools_returns_list(self, client: TestClient) -> None:
        response = client.get("/mcp/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)

    def test_get_tool_by_name(self, client: TestClient) -> None:
        response = client.get("/mcp/tools/project_list")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "project_list"
        assert "description" in data
        assert "input_schema" in data


class TestMCPResources:
    def test_list_resources(self, client: TestClient) -> None:
        response = client.get("/mcp/resources")
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        assert isinstance(data["resources"], list)

    def test_get_context_pack(self, client: TestClient) -> None:
        response = client.get("/mcp/resources/context_pack")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert isinstance(data["content"], str)
