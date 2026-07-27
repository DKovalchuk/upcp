"""Tests for Agent model, tokens, and authentication."""

import pytest
from app.identity.agents import Agent, AgentToken
from app.identity.models import User
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Agent model
# ---------------------------------------------------------------------------


class TestAgentModel:
    def test_agent_creation(self, db_session: Session) -> None:
        user = User(email="admin@example.com", password_hash="hash", display_name="Admin")
        db_session.add(user)
        db_session.flush()

        agent = Agent(
            name="code-reviewer",
            description="Reviews code for quality",
            created_by=user.id,
        )
        db_session.add(agent)
        db_session.flush()

        assert agent.id is not None
        assert agent.name == "code-reviewer"
        assert agent.description == "Reviews code for quality"
        assert agent.is_active is True
        assert agent.created_by == user.id
        assert agent.created_at is not None

    def test_agent_name_unique(self, db_session: Session) -> None:
        user = User(email="admin2@example.com", password_hash="hash", display_name="Admin2")
        db_session.add(user)
        db_session.flush()

        a1 = Agent(name="reviewer", description="First", created_by=user.id)
        a2 = Agent(name="reviewer", description="Second", created_by=user.id)
        db_session.add(a1)
        db_session.flush()

        db_session.add(a2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_agent_is_active_default_true(self, db_session: Session) -> None:
        user = User(email="admin3@example.com", password_hash="hash", display_name="Admin3")
        db_session.add(user)
        db_session.flush()

        agent = Agent(name="test-agent", description="Test", created_by=user.id)
        db_session.add(agent)
        db_session.flush()
        assert agent.is_active is True


# ---------------------------------------------------------------------------
# AgentToken model
# ---------------------------------------------------------------------------


class TestAgentTokenModel:
    def test_token_creation(self, db_session: Session) -> None:
        user = User(email="admin4@example.com", password_hash="hash", display_name="Admin4")
        db_session.add(user)
        db_session.flush()

        agent = Agent(name="token-agent", description="Test", created_by=user.id)
        db_session.add(agent)
        db_session.flush()

        token = AgentToken(
            agent_id=agent.id,
            token_hash="a" * 64,
            name="production",
            scopes=["read", "write"],
        )
        db_session.add(token)
        db_session.flush()

        assert token.id is not None
        assert token.agent_id == agent.id
        assert token.name == "production"
        assert token.revoked_at is None
        assert token.last_used_at is None
        assert token.created_at is not None

    def test_token_hash_unique(self, db_session: Session) -> None:
        user = User(email="admin5@example.com", password_hash="hash", display_name="Admin5")
        db_session.add(user)
        db_session.flush()

        agent = Agent(name="dup-token-agent", description="Test", created_by=user.id)
        db_session.add(agent)
        db_session.flush()

        t1 = AgentToken(agent_id=agent.id, token_hash="b" * 64, name="t1", scopes=[])
        t2 = AgentToken(agent_id=agent.id, token_hash="b" * 64, name="t2", scopes=[])
        db_session.add(t1)
        db_session.flush()

        db_session.add(t2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_agent_can_have_multiple_tokens(self, db_session: Session) -> None:
        user = User(email="admin6@example.com", password_hash="hash", display_name="Admin6")
        db_session.add(user)
        db_session.flush()

        agent = Agent(name="multi-token", description="Test", created_by=user.id)
        db_session.add(agent)
        db_session.flush()

        db_session.add_all(
            [
                AgentToken(agent_id=agent.id, token_hash="c" * 64, name="t1", scopes=[]),
                AgentToken(agent_id=agent.id, token_hash="d" * 64, name="t2", scopes=[]),
            ]
        )
        db_session.flush()

        tokens = db_session.query(AgentToken).filter_by(agent_id=agent.id).all()
        assert len(tokens) == 2

    def test_token_cascade_on_agent_delete(self, db_session: Session) -> None:
        user = User(email="admin7@example.com", password_hash="hash", display_name="Admin7")
        db_session.add(user)
        db_session.flush()

        agent = Agent(name="cascade-agent", description="Test", created_by=user.id)
        db_session.add(agent)
        db_session.flush()

        token = AgentToken(agent_id=agent.id, token_hash="e" * 64, name="t1", scopes=[])
        db_session.add(token)
        db_session.flush()

        db_session.delete(agent)
        db_session.flush()

        remaining = db_session.query(AgentToken).all()
        assert len(remaining) == 0
