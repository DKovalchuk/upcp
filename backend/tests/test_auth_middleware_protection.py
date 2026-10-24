"""Tests for auth middleware — protects /api/v1/ and /mcp/ routes."""

import app.identity.agents  # noqa: F401 — register Agent/AgentToken tables
from app.identity.middleware import PUBLIC_PATHS, AuthMiddleware
from app.shared.database import Base
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


def test_middleware_allows_api_with_valid_token(seed_subject) -> None:
    """Request to /api/v1/ with valid token for an existing subject → 200."""
    from app.identity.token_service import TokenService

    ts = TokenService(secret_key="test-secret")

    app = FastAPI()
    app.add_middleware(AuthMiddleware, token_service=ts)

    @app.get("/api/v1/projects")
    async def list_projects() -> dict:
        return {"items": []}

    client = TestClient(app)
    seed_subject("user-123")
    token = ts.create_access_token("user-123")
    resp = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_middleware_blocks_mcp_without_token() -> None:
    """Request to /mcp/ without token should return 401."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/mcp/tools")
    async def mcp_tools() -> dict:
        return {"tools": []}

    client = TestClient(app)
    resp = client.get("/mcp/tools")
    assert resp.status_code == 401


def test_middleware_blocks_mcp_health_without_token() -> None:
    """/mcp/health is no longer public (TASK-0148 finding 5: the entry was
    dead — no such route is registered) — unauthenticated → 401 like any
    other /mcp path."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/mcp/health")
    async def mcp_health() -> dict:
        return {"status": "ok"}

    client = TestClient(app)
    resp = client.get("/mcp/health")
    assert resp.status_code == 401


def test_middleware_allows_mcp_with_valid_token(seed_subject) -> None:
    """Request to /mcp/ with valid JWT for an existing subject → 200."""
    from app.identity.token_service import TokenService

    ts = TokenService(secret_key="test-secret")

    app = FastAPI()
    app.add_middleware(AuthMiddleware, token_service=ts)

    @app.get("/mcp/tools")
    async def mcp_tools() -> dict:
        return {"tools": []}

    client = TestClient(app)
    seed_subject("user-123")
    token = ts.create_access_token("user-123")
    resp = client.get(
        "/mcp/tools",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_middleware_allows_mcp_with_agent_token() -> None:
    """Request to /mcp/ with valid X-Agent-Token should pass."""
    from app.identity.agents import Agent, AgentToken
    from app.identity.middleware import _hash_token

    from tests.conftest import _test_engine, _TestSession

    Base.metadata.create_all(bind=_test_engine)

    # Patch SessionLocal in the database module so the middleware's lazy import
    # picks up the test DB session factory
    import app.shared.database as db_mod

    original_session_local = db_mod.SessionLocal
    db_mod.SessionLocal = _TestSession
    try:
        session = _TestSession()
        try:
            agent = Agent(name="mcp-test-agent", description="test", created_by=None)
            session.add(agent)
            session.flush()
            raw = "test-agent-token-mcp"
            token_hash = _hash_token(raw)
            tok = AgentToken(
                id="tok-mcp-test",
                agent_id=agent.id,
                token_hash=token_hash,
                name="default",
            )
            session.add(tok)
            session.commit()
        finally:
            session.close()

        app = FastAPI()
        app.add_middleware(AuthMiddleware)

        @app.get("/mcp/tools")
        async def mcp_tools() -> dict:
            return {"tools": []}

        client = TestClient(app)
        resp = client.get(
            "/mcp/tools",
            headers={"X-Agent-Token": raw},
        )
        assert resp.status_code == 200
    finally:
        db_mod.SessionLocal = original_session_local
        # Cleanup
        session = _TestSession()
        try:
            session.query(AgentToken).filter_by(id="tok-mcp-test").delete()
            session.query(Agent).filter_by(name="mcp-test-agent").delete()
            session.commit()
        finally:
            session.close()
