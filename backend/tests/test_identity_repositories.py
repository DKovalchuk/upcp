"""Identity repositories — SPEC-0029 §3.1 / TASK-0174 (red → green).

Repositories are the only NEW module allowed to touch the DB in the auth
path (AC1). Two seams, per SPEC-0029 D3:

- constructor-injected session (unit seam: ``UserRepository(session=db)``);
- session-less → ``SessionLocal`` resolved LAZILY per call (the
  ``_fetch_user_state`` test-seam precedent; the autouse conftest
  redirect lands it on the shared in-memory test DB).

Characterization of the semantics being extracted:

- ``UserRepository.get_auth_state`` mirrors ``middleware._fetch_user_state``
  byte-for-byte: ``"active" | "unknown" | "disabled"``.
- ``AgentTokenRepository.touch_last_used`` is the SINGLE write point for
  ``last_used_at`` and commits before returning (commit-before-response,
  service.py / TASK-0142) — resolving the commit-vs-flush divergence
  between middleware.py and agent_auth.py in favour of commit (AC4).
- ``AgentRepository.get`` returns the raw row; the active-check belongs
  to ``AgentTokenService``.

Session-usage rule for these tests (all sessions share one StaticPool
connection): seed rows are committed BEFORE session-less repository
calls — a per-call session's ``close()`` resets the shared connection
and would roll back uncommitted fixture work (verified empirically for
TASK-0174).
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest
from app.identity.agents import Agent, AgentToken
from app.identity.models import User
from app.identity.repositories import AgentRepository, AgentTokenRepository, UserRepository
from sqlalchemy.orm import Session

TOUCHED_AT = datetime(2026, 11, 2, 12, 0, 0, tzinfo=UTC)


def _seed_user(db: Session, *, active: bool) -> str:
    user = User(
        email=f"repo-{uuid4().hex[:10]}@test.local",
        password_hash="x" * 60,
        display_name="Repo",
        is_active=active,
    )
    db.add(user)
    db.commit()
    return str(user.id)


def _seed_token(db: Session, *, agent_active: bool = True) -> tuple[str, str, str]:
    """Seed agent + token row; returns (agent_id, token_id, token_hash)."""
    agent = Agent(
        name=f"repo-agent-{uuid4().hex[:10]}",
        is_active=agent_active,
        created_by=None,
    )
    db.add(agent)
    db.flush()
    token = AgentToken(
        agent_id=agent.id,
        token_hash="a" * 64,
        name="default",
        scopes={"read": True},
    )
    db.add(token)
    db.commit()
    return str(agent.id), str(token.id), token.token_hash


# ── UserRepository.get_auth_state — parity with _fetch_user_state ───


def test_get_auth_state_unknown_subject(db_session: Session) -> None:
    """Subject that never existed → "unknown" (middleware finding-2 semantics)."""
    assert UserRepository().get_auth_state(str(uuid4())) == "unknown"


def test_get_auth_state_active(db_session: Session) -> None:
    uid = _seed_user(db_session, active=True)
    assert UserRepository().get_auth_state(uid) == "active"


def test_get_auth_state_disabled(db_session: Session) -> None:
    uid = _seed_user(db_session, active=False)
    assert UserRepository().get_auth_state(uid) == "disabled"


def test_get_auth_state_injected_session_seam(db_session: Session) -> None:
    """Unit seam: a constructor-provided session is used as-is, no SessionLocal."""
    uid = _seed_user(db_session, active=True)
    repo = UserRepository(session=db_session)
    assert repo.get_auth_state(uid) == "active"
    assert repo.get_auth_state(str(uuid4())) == "unknown"


def test_sessionless_calls_resolve_session_local_per_call(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D3 seam: session-less repositories resolve SessionLocal lazily, once per call."""
    import app.shared.database as db_mod

    calls: list[int] = []
    real = db_mod.SessionLocal

    def spy():  # noqa: ANN202
        calls.append(1)
        return real()

    monkeypatch.setattr(db_mod, "SessionLocal", spy)
    repo = UserRepository()
    repo.get_auth_state(str(uuid4()))
    repo.get_auth_state(str(uuid4()))
    assert len(calls) == 2, f"expected one SessionLocal per call, got {len(calls)}"

    UserRepository(session=db_session).get_auth_state(str(uuid4()))
    assert len(calls) == 2, "constructor-provided session must bypass SessionLocal"


# ── AgentTokenRepository — lookup + single write point ──────────────


def test_find_by_hash_returns_matching_record(db_session: Session) -> None:
    agent_id, token_id, token_hash = _seed_token(db_session)
    found = AgentTokenRepository().find_by_hash(token_hash)
    assert found is not None
    assert str(found.id) == token_id
    assert str(found.agent_id) == agent_id
    assert found.revoked_at is None
    assert found.expires_at is None
    assert found.scopes == {"read": True}


def test_find_by_hash_unknown_returns_none(db_session: Session) -> None:
    _seed_token(db_session)
    assert AgentTokenRepository().find_by_hash("f" * 64) is None


def test_touch_last_used_commits_on_injected_session(db_session: Session) -> None:
    """AC4: the touch write COMMITs before returning — flush-only would race
    the client's next request (commit-before-response, service.py)."""
    _, token_id, token_hash = _seed_token(db_session)
    repo = AgentTokenRepository(session=db_session)
    record = repo.find_by_hash(token_hash)
    assert record is not None

    with patch.object(db_session, "commit", wraps=db_session.commit) as commit_spy:
        repo.touch_last_used(record, TOUCHED_AT)

    commit_spy.assert_called_once()
    stored = db_session.get(AgentToken, token_id)
    assert stored is not None
    assert stored.last_used_at is not None
    assert stored.last_used_at.replace(tzinfo=UTC) == TOUCHED_AT


def test_touch_last_used_sessionless_persists_only_the_timestamp(
    db_session: Session,
) -> None:
    """Single write point: last_used_at updated, sibling columns untouched."""
    _, token_id, token_hash = _seed_token(db_session)
    repo = AgentTokenRepository()
    record = repo.find_by_hash(token_hash)
    assert record is not None

    repo.touch_last_used(record, TOUCHED_AT)

    stored = db_session.get(AgentToken, token_id)
    assert stored is not None
    assert stored.last_used_at is not None
    assert stored.last_used_at.replace(tzinfo=UTC) == TOUCHED_AT
    assert stored.name == "default"
    assert stored.token_hash == token_hash


# ── AgentRepository — raw row, active-check belongs to the service ──


def test_agent_repository_get_returns_agent(db_session: Session) -> None:
    agent_id, _, _ = _seed_token(db_session)
    agent = AgentRepository().get(agent_id)
    assert agent is not None
    assert agent.is_active is True
    assert agent.name.startswith("repo-agent-")


def test_agent_repository_get_unknown_returns_none(db_session: Session) -> None:
    _seed_token(db_session)
    assert AgentRepository().get(str(uuid4())) is None


def test_agent_repository_get_returns_inactive_agent(db_session: Session) -> None:
    """The repository returns the raw row — is_active filtering is the
    service's lifecycle decision, not the query's."""
    agent_id, _, _ = _seed_token(db_session, agent_active=False)
    agent = AgentRepository().get(agent_id)
    assert agent is not None
    assert agent.is_active is False
