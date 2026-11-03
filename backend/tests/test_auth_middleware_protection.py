"""Tests for the web-surface auth guard — protects /api/v1/ and /mcp/ routes.

TASK-0169: the harness moved off ``app.add_middleware(AuthMiddleware)`` to
dependency-based protection (``FastAPI(dependencies=[Depends(web_auth)])`` /
``include_router(..., dependencies=[Depends(get_current_agent)])``); every
assertion (status, detail, headers) is unchanged — the migration is
mechanism-only. ``PUBLIC_PATHS`` stays until the middleware retires in
TASK-0170 (with ``tests/test_public_paths.py``).
"""

import app.identity.agents  # noqa: F401 — register Agent/AgentToken tables
import pytest
from app.identity.agent_auth import get_current_agent
from app.identity.auth import _get_token_service
from app.identity.middleware import PUBLIC_PATHS
from app.identity.web_auth import web_auth
from app.shared.config import get_settings
from app.shared.database import Base
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _enable_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """The guard is inert under conftest's hermetic disable_auth=true — turn it on.

    Mirrors the old harness implicitly getting a mounted AuthMiddleware
    (main.py mounts it only when auth is enabled).
    """
    monkeypatch.setattr(get_settings(), "disable_auth", False)


def test_public_paths_are_exempt() -> None:
    """Public paths should not require auth."""
    assert "/health" in PUBLIC_PATHS
    assert "/api/v1/health" in PUBLIC_PATHS
    assert "/auth/setup" in PUBLIC_PATHS
    assert "/auth/login" in PUBLIC_PATHS
    assert "/auth/refresh" in PUBLIC_PATHS


def test_middleware_allows_public_path() -> None:
    """Public path: declared WITHOUT the auth dependency → reachable (D2).

    Contrast: the protected router in the same app is denied — the public
    path is exempt by composition, not by a runtime path dictionary.
    """
    app = FastAPI()

    protected = APIRouter()

    @protected.get("/api/v1/projects")
    async def list_projects() -> dict:
        return {"items": []}

    app.include_router(protected, dependencies=[Depends(web_auth)])

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert client.get("/api/v1/projects").status_code == 401


def test_middleware_blocks_api_without_token() -> None:
    """Request to /api/v1/ without token should return 401."""
    app = FastAPI(dependencies=[Depends(web_auth)])

    @app.get("/api/v1/projects")
    async def list_projects() -> dict:
        return {"items": []}

    client = TestClient(app)
    resp = client.get("/api/v1/projects")
    assert resp.status_code == 401


def test_middleware_blocks_api_with_invalid_token() -> None:
    """Request to /api/v1/ with invalid token should return 401."""
    app = FastAPI(dependencies=[Depends(web_auth)])

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

    app = FastAPI(dependencies=[Depends(web_auth)])
    app.dependency_overrides[_get_token_service] = lambda: ts

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
    app = FastAPI(dependencies=[Depends(web_auth)])

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
    app = FastAPI(dependencies=[Depends(web_auth)])

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

    app = FastAPI(dependencies=[Depends(web_auth)])
    app.dependency_overrides[_get_token_service] = lambda: ts

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
    """Request to /mcp/ with valid X-Agent-Token should pass.

    Seam: the middleware's agent branch → ``Depends(get_current_agent)``
    (the interim agent guard; TASK-0170 blankets the AGENT surface with
    ``agent_auth``). ``SessionLocal`` is the conftest autouse seam.
    """
    from app.identity.agent_token_service import _hash_token
    from app.identity.agents import Agent, AgentToken

    from tests.conftest import _test_engine, _TestSession

    Base.metadata.create_all(bind=_test_engine)

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

    try:
        app = FastAPI(dependencies=[Depends(get_current_agent)])

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
        session = _TestSession()
        try:
            session.query(AgentToken).filter_by(id="tok-mcp-test").delete()
            session.query(Agent).filter_by(name="mcp-test-agent").delete()
            session.commit()
        finally:
            session.close()
