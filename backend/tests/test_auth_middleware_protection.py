"""Tests for auth middleware — protects /api/v1/ routes."""

from app.identity.middleware import PUBLIC_PATHS, AuthMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_public_paths_are_exempt() -> None:
    """Public paths should not require auth."""
    assert "/health" in PUBLIC_PATHS
    assert "/api/v1/health" in PUBLIC_PATHS
    assert "/auth/setup" in PUBLIC_PATHS
    assert "/auth/login" in PUBLIC_PATHS
    assert "/auth/refresh" in PUBLIC_PATHS


def test_middleware_allows_public_path() -> None:
    """Request to public path should pass through."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200


def test_middleware_blocks_api_without_token() -> None:
    """Request to /api/v1/ without token should return 401."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/api/v1/projects")
    async def list_projects() -> dict:
        return {"items": []}

    client = TestClient(app)
    resp = client.get("/api/v1/projects")
    assert resp.status_code == 401


def test_middleware_blocks_api_with_invalid_token() -> None:
    """Request to /api/v1/ with invalid token should return 401."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/api/v1/projects")
    async def list_projects() -> dict:
        return {"items": []}

    client = TestClient(app)
    resp = client.get(
        "/api/v1/projects",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert resp.status_code == 401


def test_middleware_allows_api_with_valid_token() -> None:
    """Request to /api/v1/ with valid token should pass."""
    from app.identity.token_service import TokenService

    ts = TokenService(secret_key="test-secret")

    app = FastAPI()
    app.add_middleware(AuthMiddleware, token_service=ts)

    @app.get("/api/v1/projects")
    async def list_projects() -> dict:
        return {"items": []}

    client = TestClient(app)
    token = ts.create_access_token("user-123")
    resp = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_middleware_skips_non_api_routes() -> None:
    """Non-API routes should not require auth."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/mcp/tools")
    async def mcp_tools() -> dict:
        return {"tools": []}

    client = TestClient(app)
    resp = client.get("/mcp/tools")
    assert resp.status_code == 200
