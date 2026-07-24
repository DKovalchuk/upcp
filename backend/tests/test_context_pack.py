"""Tests for context pack generator."""
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


class TestContextPack:
    def test_context_pack_resource_exists(self, client: TestClient) -> None:
        response = client.get("/mcp/resources/context_pack")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert isinstance(data["content"], str)

    def test_context_pack_contains_project_info(self, client: TestClient) -> None:
        response = client.get("/mcp/resources/context_pack")
        assert response.status_code == 200
        data = response.json()
        content = data["content"]
        assert "# Context Pack" in content

    def test_context_pack_via_jsonrpc(self, client: TestClient) -> None:
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "resources/read",
                "params": {
                    "uri": "context_pack://project",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "contents" in data["result"]
        assert len(data["result"]["contents"]) == 1
        assert "text" in data["result"]["contents"][0]