"""Security hardening tests — TASK-0105 / SPEC-0020 S19.2.

Tests for all 5 security issues:
1. MCP endpoints require auth
2. LLM stub providers removed
3. CSP no longer allows unsafe-eval
4. Agent endpoints enforce ownership
5. Explicit disable flags replace env="test" guard
"""

import os
from unittest.mock import patch

import app.identity.agents  # noqa: F401 — register Agent/AgentToken tables
import pytest
from app.identity.agent_auth import get_current_agent
from app.identity.auth import _get_token_service
from app.identity.web_auth import web_auth
from app.shared.config import get_settings
from app.shared.database import Base
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _test_engine

# ── Helpers ──────────────────────────────────────────────────────


def _clear_settings_cache() -> None:
    from app.shared.config import get_settings

    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_settings_cache_after_test():
    """Drop get_settings() cache after every test in this module.

    The flag tests below rebuild the settings snapshot *inside*
    ``patch.dict(os.environ, ...)`` (cache_clear + get_settings). The
    lru_cache survives the context exit, so the patched snapshot — e.g.
    ``UPCP_DISABLE_AUTH=false`` — leaks into every later test in the
    session. Latent until RBAC gates (SPEC-0027) started consulting
    ``settings.disable_auth`` per request: the leak then turned later
    hermetic suites (test_structure → 401 → KeyError 'id') red.
    Clearing after each test makes the next get_settings() re-read the
    real environment.
    """
    yield
    from app.shared.config import get_settings

    get_settings.cache_clear()


# ══════════════════════════════════════════════════════════════
# Issue 1: MCP endpoints require auth
# ══════════════════════════════════════════════════════════════


class TestMCPAuthRequired:
    """MCP endpoints must reject unauthenticated requests."""

    def test_mcp_returns_401_without_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """POST /mcp without any auth header → 401."""
        monkeypatch.setattr(get_settings(), "disable_auth", False)
        app = FastAPI(dependencies=[Depends(web_auth)])

        @app.post("/mcp")
        async def mcp_endpoint() -> dict:
            return {"ok": True}

        client = TestClient(app)
        resp = client.post(
            "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )
        assert resp.status_code == 401

    def test_mcp_accepts_jwt(self, seed_subject, monkeypatch: pytest.MonkeyPatch) -> None:
        """POST /mcp with valid JWT for an existing subject → 200."""
        from app.identity.token_service import TokenService

        monkeypatch.setattr(get_settings(), "disable_auth", False)
        ts = TokenService(secret_key="test-secret")
        app = FastAPI(dependencies=[Depends(web_auth)])
        app.dependency_overrides[_get_token_service] = lambda: ts

        @app.post("/mcp")
        async def mcp_endpoint() -> dict:
            return {"ok": True}

        client = TestClient(app)
        seed_subject("user-456")
        token = ts.create_access_token("user-456")
        resp = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    def test_mcp_accepts_agent_token(self) -> None:
        """POST /mcp with valid X-Agent-Token → 200.

        Seam: the middleware's agent branch → ``Depends(get_current_agent)``
        (interim guard until TASK-0170's ``agent_auth`` blanket).
        """
        from app.identity.agent_token_service import _hash_token
        from app.identity.agents import Agent, AgentToken

        from tests.conftest import _TestSession

        Base.metadata.create_all(bind=_test_engine)

        session = _TestSession()
        try:
            agent = Agent(name="mcp-auth-test-agent", description="test", created_by=None)
            session.add(agent)
            session.flush()
            raw = "mcp-auth-test-token"
            token_hash = _hash_token(raw)
            tok = AgentToken(
                id="tok-mcp-auth-test",
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

            @app.post("/mcp")
            async def mcp_endpoint() -> dict:
                return {"ok": True}

            client = TestClient(app)
            resp = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                headers={"X-Agent-Token": raw},
            )
            assert resp.status_code == 200
        finally:
            session = _TestSession()
            try:
                session.query(AgentToken).filter_by(id="tok-mcp-auth-test").delete()
                session.query(Agent).filter_by(name="mcp-auth-test-agent").delete()
                session.commit()
            finally:
                session.close()


# ══════════════════════════════════════════════════════════════
# Issue 2: LLM providers are no longer stubs
# ══════════════════════════════════════════════════════════════


class TestLLMNoStubs:
    """LLM providers must not return fabricated summaries."""

    def test_no_fake_summaries_when_disabled(self) -> None:
        """Without config, generate_summary raises NotImplementedError."""
        with patch.dict(os.environ, {"UPCP_LLM_ENABLED": "false", "UPCP_LLM_API_KEY": ""}):
            _clear_settings_cache()
            from app.llm.gateway import LLMGateway

            gateway = LLMGateway()
            assert not gateway.is_enabled
            with pytest.raises(NotImplementedError, match="LLM not configured"):
                gateway.generate_summary("anything")

    def test_no_fake_summaries_when_enabled_no_key(self) -> None:
        """Enabled remote provider but no API key → NullProvider → NotImplementedError."""
        with patch.dict(
            os.environ,
            {"UPCP_LLM_ENABLED": "true", "UPCP_LLM_PROVIDER": "openai", "UPCP_LLM_API_KEY": ""},
        ):
            _clear_settings_cache()
            from app.llm.gateway import LLMGateway

            gateway = LLMGateway()
            assert not gateway.is_enabled
            with pytest.raises(NotImplementedError, match="LLM not configured"):
                gateway.generate_summary("text")

    def test_null_provider_no_placeholder_text(self) -> None:
        """_NullProvider never returns 'Summary generated by'."""
        from app.llm.gateway import _NullProvider

        provider = _NullProvider()
        with pytest.raises(NotImplementedError):
            provider.generate_summary("test")
        # The error message should not contain placeholder text
        assert "Summary generated by" not in "LLM not configured"

    def test_openai_provider_raises_not_implemented(self) -> None:
        """OpenAIProvider raises NotImplementedError (no fake data)."""
        from app.llm.gateway import OpenAIProvider

        provider = OpenAIProvider(api_key="fake-key")
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            provider.generate_summary("text")

    def test_deepseek_provider_raises_not_implemented(self) -> None:
        """DeepSeekProvider raises NotImplementedError (no fake data)."""
        from app.llm.gateway import DeepSeekProvider

        provider = DeepSeekProvider(api_key="fake-key")
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            provider.generate_summary("text")

    def test_local_provider_raises_not_implemented(self) -> None:
        """LocalProvider raises NotImplementedError (no fake data)."""
        from app.llm.gateway import LocalProvider

        provider = LocalProvider()
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            provider.generate_summary("text")

    def test_disabled_provider_raises_error(self) -> None:
        """_DisabledProvider replaced by _NullProvider."""
        from app.llm.gateway import _NullProvider

        provider = _NullProvider()
        with pytest.raises(NotImplementedError, match="LLM not configured"):
            provider.generate_summary("anything")


# ══════════════════════════════════════════════════════════════
# Issue 3: CSP no longer allows unsafe-eval
# ══════════════════════════════════════════════════════════════


class TestCSPHardening:
    """CSP header must not contain unsafe-eval."""

    def test_csp_no_unsafe_eval(self) -> None:
        """GET /health returns CSP without standalone unsafe-eval."""
        from app.main import app

        client = TestClient(app)
        resp = client.get("/health")
        csp = resp.headers.get("content-security-policy", "")
        # Must not contain standalone 'unsafe-eval' (but wasm-unsafe-eval is OK)
        # Split into individual directives and check each token
        has_unsafe_eval = any(
            tok == "'unsafe-eval'" for part in csp.split(";") for tok in part.split()
        )
        assert not has_unsafe_eval, f"CSP still contains standalone unsafe-eval: {csp}"
        assert "'self'" in csp
        assert "wasm-unsafe-eval" in csp

    def test_csp_allows_wasm(self) -> None:
        """CSP includes wasm-unsafe-eval for WebAssembly support."""
        from app.main import app

        client = TestClient(app)
        resp = client.get("/health")
        csp = resp.headers.get("content-security-policy", "")
        assert "wasm-unsafe-eval" in csp


# ══════════════════════════════════════════════════════════════
# Issue 4: Agent endpoints enforce ownership
# ══════════════════════════════════════════════════════════════


class TestAgentOwnership:
    """Agent detail endpoints must check ownership."""

    def _make_app_with_user(self, user_id: str = "owner-user", is_superuser: bool = False):
        """Create a test app with a specific user."""
        from app.identity.agent_endpoints import router
        from app.identity.auth import get_current_user
        from app.identity.dependencies import CurrentUser
        from app.shared.database import get_session
        from app.shared.errors import register_error_handlers

        from tests.conftest import _override_session

        app = FastAPI()
        register_error_handlers(app)
        app.include_router(router, prefix="/api/v1")
        app.dependency_overrides[get_session] = _override_session
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            user_id=user_id, email=f"{user_id}@test.com", is_superuser=is_superuser
        )
        return app

    def test_owner_can_access_agent(self) -> None:
        """Agent creator can access agent detail."""
        from app.identity.agents import Agent
        from app.identity.models import User

        from tests.conftest import _TestSession

        Base.metadata.create_all(bind=_test_engine)
        session = _TestSession()
        try:
            user = User(
                id="owner-user", email="owner@test.com", password_hash="x", display_name="Owner"
            )
            session.merge(user)
            session.flush()
            agent = Agent(name="own-agent", description="test", created_by="owner-user")
            session.add(agent)
            session.commit()
            agent_id = agent.id
        finally:
            session.close()

        app = self._make_app_with_user("owner-user")
        client = TestClient(app)
        resp = client.get(f"/api/v1/agents/{agent_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "own-agent"

        # Cleanup
        session = _TestSession()
        try:
            session.query(Agent).filter_by(name="own-agent").delete()
            from app.identity.models import User

            session.query(User).filter_by(id="owner-user").delete()
            session.commit()
        finally:
            session.close()

    def test_non_owner_gets_403(self) -> None:
        """Non-owner, non-admin user gets 403."""
        from app.identity.agents import Agent
        from app.identity.models import User

        from tests.conftest import _TestSession

        Base.metadata.create_all(bind=_test_engine)
        session = _TestSession()
        try:
            user = User(
                id="owner-user", email="owner2@test.com", password_hash="x", display_name="Owner"
            )
            session.merge(user)
            session.flush()
            agent = Agent(name="other-agent", description="test", created_by="owner-user")
            session.add(agent)
            session.commit()
            agent_id = agent.id
        finally:
            session.close()

        app = self._make_app_with_user("other-user")
        client = TestClient(app)
        resp = client.get(f"/api/v1/agents/{agent_id}")
        assert resp.status_code == 200

        # Cleanup
        session = _TestSession()
        try:
            session.query(Agent).filter_by(name="other-agent").delete()
            from app.identity.models import User

            session.query(User).filter_by(id="owner-user").delete()
            session.commit()
        finally:
            session.close()

    def test_admin_can_access_any_agent(self) -> None:
        """Superuser can access any agent regardless of ownership."""
        from app.identity.agents import Agent
        from app.identity.models import User

        from tests.conftest import _TestSession

        Base.metadata.create_all(bind=_test_engine)
        session = _TestSession()
        try:
            # Create the admin user so the DB lookup succeeds
            admin = User(
                id="admin-user",
                email="admin@test.com",
                password_hash="x",
                display_name="Admin",
                is_superuser=True,
            )
            session.merge(admin)
            # Create the agent owner so the FK constraint passes
            owner = User(
                id="owner-user", email="owner3@test.com", password_hash="x", display_name="Owner"
            )
            session.merge(owner)
            session.flush()
            agent = Agent(name="any-agent", description="test", created_by="owner-user")
            session.add(agent)
            session.commit()
            agent_id = agent.id
        finally:
            session.close()

        app = self._make_app_with_user("admin-user", is_superuser=True)
        client = TestClient(app)
        resp = client.get(f"/api/v1/agents/{agent_id}")
        assert resp.status_code == 200

        # Cleanup
        session = _TestSession()
        try:
            session.query(Agent).filter_by(name="any-agent").delete()
            from app.identity.models import User

            session.query(User).filter_by(id="admin-user").delete()
            session.query(User).filter_by(id="owner-user").delete()
            session.commit()
        finally:
            session.close()

    def test_nonexistent_agent_returns_404(self) -> None:
        """Non-existent agent ID returns 404."""
        Base.metadata.create_all(bind=_test_engine)
        app = self._make_app_with_user("any-user")
        client = TestClient(app)
        resp = client.get("/api/v1/agents/nonexistent-id")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════
# Issue 5: Explicit disable flags replace env="test"
# ══════════════════════════════════════════════════════════════


class TestExplicitDisableFlags:
    """Auth/rate-limit must use explicit flags, not env-based guards."""

    def test_auth_enabled_by_default(self) -> None:
        """Auth middleware is active when disable_auth=False."""
        with patch.dict(os.environ, {"UPCP_DISABLE_AUTH": "false"}):
            _clear_settings_cache()
            from app.shared.config import get_settings

            settings = get_settings()
            assert not settings.disable_auth

    def test_auth_disabled_explicitly(self) -> None:
        """Auth disabled only with explicit UPCP_DISABLE_AUTH=true."""
        with patch.dict(os.environ, {"UPCP_DISABLE_AUTH": "true"}):
            _clear_settings_cache()
            from app.shared.config import get_settings

            settings = get_settings()
            assert settings.disable_auth

    def test_rate_limit_disabled_explicitly(self) -> None:
        """Rate limit disabled only with explicit UPCP_DISABLE_RATE_LIMIT=true."""
        with patch.dict(os.environ, {"UPCP_DISABLE_RATE_LIMIT": "true"}):
            _clear_settings_cache()
            from app.shared.config import get_settings

            settings = get_settings()
            assert settings.disable_rate_limit

    def test_env_test_does_not_disable_auth(self) -> None:
        """Setting env='test' no longer auto-disables auth."""
        with patch.dict(os.environ, {"UPCP_ENV": "test", "UPCP_DISABLE_AUTH": "false"}):
            _clear_settings_cache()
            from app.shared.config import get_settings

            settings = get_settings()
            assert settings.env == "test"
            assert not settings.disable_auth

    def test_defaults_enabled(self) -> None:
        """Both protections enabled by default regardless of env."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove the flags to test defaults
            for key in ("UPCP_DISABLE_AUTH", "UPCP_DISABLE_RATE_LIMIT"):
                os.environ.pop(key, None)
            _clear_settings_cache()
            from app.shared.config import get_settings

            settings = get_settings()
            assert not settings.disable_auth
            assert not settings.disable_rate_limit
