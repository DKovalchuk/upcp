"""AgentTokenService — SPEC-0029 §3.4 / TASK-0174 (red → green).

Lifecycle verification extracted from the two duplicated implementations
(middleware agent branch + agent_auth.get_current_agent), preserving
their outcomes (D4 parity):

- unknown hash / revoked / expired / agent missing / agent inactive →
  None (consumers map to their existing 401 shapes);
- valid → touch ``last_used_at`` ONCE through the repository (AC4 single
  write point) and return an ``AgentPrincipal``;
- expiry edge is a strict ``<`` (``expires_at == now`` is still valid —
  middleware semantics), with tz-naive stored values interpreted as UTC
  (SQLite drops tzinfo; prod Postgres round-trips — behavior unchanged
  there, TypeError on SQLite fixed);
- WRITE SEMANTICS: the touch COMMITS (commit-before-response,
  service.py / TASK-0142) — this resolves the middleware-``commit()`` vs
  agent_auth-``flush()`` divergence in favour of commit, so the very next
  request observes ``last_used_at`` (regression at the end of this file).

Single ``sha256`` helper lives with the service (AC5 dedupe lands fully
in TASK-0175/0170 when consumers are rewired).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from app.identity.agent_token_service import AgentPrincipal, AgentTokenService
from app.identity.agents import Agent, AgentToken
from app.identity.repositories import AgentRepository, AgentTokenRepository
from sqlalchemy.orm import Session

NOW = datetime(2026, 11, 2, 12, 0, 0, tzinfo=UTC)
RAW = "raw-agent-token"
RAW_HASH = hashlib.sha256(RAW.encode()).hexdigest()


def _record(**overrides: object) -> SimpleNamespace:
    base: dict[str, object] = {
        "agent_id": "agent-1",
        "token_hash": RAW_HASH,
        "scopes": None,
        "revoked_at": None,
        "expires_at": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _agent(*, is_active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(id="agent-1", name="bot", is_active=is_active)


class _StubTokenRepository:
    def __init__(self, record: SimpleNamespace | None) -> None:
        self.record = record
        self.hashes: list[str] = []
        self.touched: list[datetime] = []

    def find_by_hash(self, token_hash: str) -> SimpleNamespace | None:
        self.hashes.append(token_hash)
        return self.record

    def touch_last_used(self, record: SimpleNamespace, when: datetime) -> None:
        self.touched.append(when)


class _StubAgentRepository:
    def __init__(self, agent: SimpleNamespace | None) -> None:
        self.agent = agent
        self.gets: list[str] = []

    def get(self, agent_id: str) -> SimpleNamespace | None:
        self.gets.append(agent_id)
        return self.agent


def _service(
    record: SimpleNamespace | None, agent: SimpleNamespace | None = ...
) -> tuple[AgentTokenService, _StubTokenRepository, _StubAgentRepository]:
    tokens = _StubTokenRepository(record)
    agents = _StubAgentRepository(_agent() if agent is ... else agent)
    return AgentTokenService(tokens, agents), tokens, agents  # type: ignore[arg-type]


# ── Unit matrix: valid + lifecycle rejections ───────────────────────


def test_valid_token_returns_principal_and_touches_once() -> None:
    record = _record(scopes={"read": True})
    service, tokens, agents = _service(record)

    principal = service.verify(RAW, now=NOW)

    assert isinstance(principal, AgentPrincipal)
    assert principal.agent_id == "agent-1"
    assert principal.name == "bot"
    assert principal.scopes == {"read": True}
    assert tokens.hashes == [RAW_HASH], "single sha256 of the raw token"
    assert agents.gets == ["agent-1"]
    assert tokens.touched == [NOW], "exactly one touch, stamped with the given clock"


def test_unknown_token_rejected_without_touch() -> None:
    service, tokens, agents = _service(None)
    assert service.verify(RAW, now=NOW) is None
    assert tokens.touched == []
    assert agents.gets == [], "a dead hash must not reach the agent lookup"


def test_revoked_token_rejected_without_touch() -> None:
    service, tokens, _ = _service(_record(revoked_at=NOW))
    assert service.verify(RAW, now=NOW) is None
    assert tokens.touched == []


def test_expired_token_rejected_without_touch() -> None:
    service, tokens, _ = _service(_record(expires_at=NOW))
    assert service.verify(RAW, now=NOW.replace(year=2027)) is None
    assert tokens.touched == []


def test_expiry_boundary_equals_now_is_still_valid() -> None:
    """Strict ``<`` parity: at the exact expiry instant the token verifies."""
    service, tokens, _ = _service(_record(expires_at=NOW))
    principal = service.verify(RAW, now=NOW)
    assert principal is not None
    assert tokens.touched == [NOW]


def test_naive_expiry_datetimes_treated_as_utc() -> None:
    """SQLite returns tz-naive datetimes — must compare, not raise TypeError."""
    past_service, _, _ = _service(_record(expires_at=datetime(2026, 1, 1, 0, 0, 0)))
    assert past_service.verify(RAW, now=NOW) is None

    future_service, future_tokens, _ = _service(_record(expires_at=datetime(2027, 1, 1, 0, 0, 0)))
    assert future_service.verify(RAW, now=datetime(2026, 6, 1)) is not None
    assert future_tokens.touched == [datetime(2026, 6, 1, tzinfo=UTC)]


def test_missing_agent_rejected_without_touch() -> None:
    service, tokens, agents = _service(_record(), agent=None)
    assert service.verify(RAW, now=NOW) is None
    assert tokens.touched == []


def test_inactive_agent_rejected_without_touch() -> None:
    service, tokens, agents = _service(_record(), agent=_agent(is_active=False))
    assert service.verify(RAW, now=NOW) is None
    assert tokens.touched == []


def test_default_clock_used_when_now_omitted() -> None:
    expired = _record(expires_at=datetime(2000, 1, 1, tzinfo=UTC))
    expired_service, _, _ = _service(expired)
    assert expired_service.verify(RAW) is None

    fresh = _record(expires_at=datetime(2100, 1, 1, tzinfo=UTC))
    fresh_service, fresh_tokens, _ = _service(fresh)
    assert fresh_service.verify(RAW) is not None
    assert len(fresh_tokens.touched) == 1


# ── Integration: real DB through the repository seam ────────────────


def _seed_token(
    db: Session, *, expires_at: datetime | None = None, agent_active: bool = True
) -> tuple[str, str]:
    agent = Agent(name=f"ats-agent-{agent_active}-{expires_at}", is_active=agent_active)
    db.add(agent)
    db.flush()
    token = AgentToken(
        agent_id=agent.id,
        token_hash=RAW_HASH,
        name="default",
        scopes={"read": True},
        expires_at=expires_at,
    )
    db.add(token)
    db.commit()
    return str(agent.id), str(token.id)


def test_verify_real_db_roundtrip_touches_last_used(db_session: Session) -> None:
    agent_id, token_id = _seed_token(db_session)
    service = AgentTokenService(AgentTokenRepository(), AgentRepository())

    principal = service.verify(RAW, now=NOW)

    assert principal is not None
    assert principal.agent_id == agent_id
    assert principal.scopes == {"read": True}
    stored = db_session.get(AgentToken, token_id)
    assert stored is not None and stored.last_used_at is not None
    assert abs((stored.last_used_at - NOW.replace(tzinfo=None)).total_seconds()) < 1


def test_verify_real_db_expired_token_rejected(db_session: Session) -> None:
    """Real round-trip: stored value comes back naive from SQLite and must
    still classify as expired instead of raising TypeError."""
    _, token_id = _seed_token(db_session, expires_at=NOW.replace(year=2025))
    service = AgentTokenService(AgentTokenRepository(), AgentRepository())

    assert service.verify(RAW, now=NOW) is None
    stored = db_session.get(AgentToken, token_id)
    assert stored is not None and stored.last_used_at is None


def test_verify_real_db_inactive_agent_rejected(db_session: Session) -> None:
    _seed_token(db_session, agent_active=False)
    service = AgentTokenService(AgentTokenRepository(), AgentRepository())
    assert service.verify(RAW, now=NOW) is None


def test_verify_real_db_unknown_hash_rejected(db_session: Session) -> None:
    _seed_token(db_session)
    service = AgentTokenService(AgentTokenRepository(), AgentRepository())
    assert service.verify("some-other-token", now=NOW) is None


# ── AC4: commit-before-response regression ──────────────────────────


def test_last_used_at_committed_before_response(db_session: Session) -> None:
    """AC4: verify() COMMITS the touch — flush-only would race the client's
    next request (TASK-0142). ``Session.commit`` is invoked exactly once
    during ``verify()`` (spy); the surviving-write proof complements it in
    ``test_verify_real_db_roundtrip_touches_last_used`` — a session-less
    repository closes (and thus rolls back) right after the write, so a
    flush-only value could never be read back.

    An independent-connection probe would need a second engine, which the
    engine-dedup invariant (``test_engine_dedup.py``) forbids here —
    shared-engine deviation recorded in the task evidence."""
    _, token_id = _seed_token(db_session)
    service = AgentTokenService(
        AgentTokenRepository(session=db_session),
        AgentRepository(session=db_session),
    )

    with patch.object(db_session, "commit", wraps=db_session.commit) as commit_spy:
        assert service.verify(RAW, now=NOW) is not None

    assert commit_spy.call_count == 1, "verify() must commit the touch, not flush it"
    stored = db_session.get(AgentToken, token_id)
    assert stored is not None and stored.last_used_at is not None
