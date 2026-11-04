"""get_current_agent over AgentTokenService — SPEC-0029 §3.5 / TASK-0175.

The dependency stops hashing/querying/flushing itself: verification,
rejection classification and the committed ``last_used_at`` touch live in
``AgentTokenService`` (TASK-0174 invariants). The ADDITIVE
``verify_detailed`` API returns ``AgentPrincipal | AgentTokenRejection``
and this module maps the four reasons onto the historical 401 details
byte-for-byte; ``verify()`` stays a thin wrapper (its existing tests keep
passing).

WRITE TIMING (intended change, TASK-0174 AC4): the touch now COMMITS
inside the service instead of ``flush()`` + teardown-commit — pinned by
the commit-spy test, which is red before the rewiring. The service is
built request-scoped over the request session
(``_get_agent_token_service``), so the commit lands before the response.

Parity guards (green from the start) pin the historical 401 shapes. New
symbols are imported inside tests so the file collects before the
implementation exists.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from app.identity.agent_auth import get_current_agent
from app.identity.agent_token_service import AgentPrincipal, AgentTokenService
from app.identity.agents import Agent, AgentToken
from app.identity.dependencies import CurrentAgent
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

RAW = "raw-agent-token-unification"
NOW = datetime(2026, 11, 2, 12, 0, 0, tzinfo=UTC)
PAST = datetime(2020, 1, 1, tzinfo=UTC)


def _record(**overrides: object) -> SimpleNamespace:
    base: dict[str, object] = {
        "agent_id": "a1",
        "token_hash": hashlib.sha256(RAW.encode()).hexdigest(),
        "scopes": None,
        "revoked_at": None,
        "expires_at": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _agent(*, active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(id="a1", name="bot", is_active=active)


class _StubTokens:
    def __init__(self, record: SimpleNamespace | None) -> None:
        self.record = record
        self.touched: list[datetime] = []

    def find_by_hash(self, token_hash: str) -> SimpleNamespace | None:
        return self.record

    def touch_last_used(self, record: SimpleNamespace, when: datetime) -> None:
        self.touched.append(when)


class _StubAgents:
    def __init__(self, agent: SimpleNamespace | None) -> None:
        self.agent = agent

    def get(self, agent_id: str) -> SimpleNamespace | None:
        return self.agent


def _service(
    record: SimpleNamespace | None, agent: SimpleNamespace | None = ...
) -> tuple[AgentTokenService, _StubTokens]:
    tokens = _StubTokens(record)
    agents = _StubAgents(_agent() if agent is ... else agent)
    return AgentTokenService(tokens, agents), tokens  # type: ignore[arg-type]


# ── verify_detailed: the additive reason API (red before TASK-0175) ─


@pytest.mark.parametrize(
    "record,agent,reason",
    [
        (None, ..., "unknown"),
        (_record(revoked_at=NOW), ..., "revoked"),
        (_record(expires_at=PAST), ..., "expired"),
        (_record(), None, "agent_inactive"),
        (_record(), _agent(active=False), "agent_inactive"),
    ],
)
def test_verify_detailed_classifies_every_rejection(
    record: SimpleNamespace | None,
    agent: SimpleNamespace | None,
    reason: str,
) -> None:
    from app.identity.agent_token_service import AgentTokenRejection

    service, tokens = _service(record, agent)
    result = service.verify_detailed(RAW, now=NOW)
    assert isinstance(result, AgentTokenRejection), f"expected rejection, got {result!r}"
    assert result.reason == reason
    assert tokens.touched == [], "rejections never stamp last_used_at"

    # verify() wrapper parity: same lifecycle outcome as before (None).
    wrapper, _ = _service(record, agent)
    assert wrapper.verify(RAW, now=NOW) is None


def test_verify_detailed_success_returns_principal_and_touches() -> None:
    service, tokens = _service(_record(scopes={"read": True}))
    result = service.verify_detailed(RAW, now=NOW)
    assert isinstance(result, AgentPrincipal)
    assert (result.agent_id, result.name) == ("a1", "bot")
    assert result.scopes == {"read": True}
    assert tokens.touched == [NOW], "exactly one committed touch on success"

    # verify() wrapper stays equivalent for the success path too.
    wrapper, _ = _service(_record(scopes={"read": True}))
    principal = wrapper.verify(RAW, now=NOW)
    assert isinstance(principal, AgentPrincipal)
    assert principal.scopes == {"read": True}


def test_verify_detailed_propagates_db_errors() -> None:
    """DB failures are not rejections — they propagate (service contract)."""

    class _Boom:
        def find_by_hash(self, token_hash: str):  # noqa: ANN201
            raise RuntimeError("db down")

        def touch_last_used(self, record: object, when: datetime) -> None:  # noqa: ANN001
            raise AssertionError("unreachable")

    service = AgentTokenService(_Boom(), _StubAgents(_agent()))  # type: ignore[arg-type]
    with pytest.raises(RuntimeError):
        service.verify_detailed(RAW)
    with pytest.raises(RuntimeError):
        service.verify(RAW)


# ── Dependency: historical 401 shapes + principal fields ────────────


@pytest.fixture()
def seeded(db_session: Session) -> tuple[str, str, str]:
    """Active agent + committed token: (raw_token, agent_id, token_id)."""
    agent = Agent(name=f"unif-agent-{uuid4().hex[:8]}", description="dep", created_by=None)
    db_session.add(agent)
    db_session.flush()
    raw = "unif-" + uuid4().hex
    token = AgentToken(
        agent_id=agent.id,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        name="default",
        scopes={"read": True, "write": False},
    )
    db_session.add(token)
    db_session.commit()
    return raw, str(agent.id), str(token.id)


@pytest.fixture()
def client(db_session: Session, seeded: tuple[str, str, str]) -> TestClient:
    """Minimal app exposing get_current_agent; NO teardown commit here so
    the service's own commit is observable (commit-timing test)."""
    from app.shared.database import get_session

    app = FastAPI()

    @app.get("/protected-agent")
    async def protected(agent: CurrentAgent = Depends(get_current_agent)) -> dict[str, object]:
        return {"agent_id": agent.agent_id, "name": agent.name, "scopes": agent.scopes}

    def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    return TestClient(app)


def _hdr(raw: str) -> dict[str, str]:
    return {"X-Agent-Token": raw}


def test_valid_token_returns_current_agent_with_scopes(
    client: TestClient, seeded: tuple[str, str, str]
) -> None:
    raw, agent_id, _ = seeded
    resp = client.get("/protected-agent", headers=_hdr(raw))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["agent_id"] == agent_id
    assert body["name"].startswith("unif-agent-")
    assert body["scopes"] == {"read": True, "write": False}


def test_missing_header_rejected(client: TestClient) -> None:
    resp = client.get("/protected-agent")
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Missing agent token"


def test_unknown_token_rejected_with_historical_detail(client: TestClient) -> None:
    resp = client.get("/protected-agent", headers=_hdr("never-issued-token"))
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Invalid agent token"


def test_revoked_token_rejected_with_historical_detail(
    db_session: Session, client: TestClient, seeded: tuple[str, str, str]
) -> None:
    raw, _, token_id = seeded
    db_session.query(AgentToken).filter_by(id=token_id).update({"revoked_at": datetime(2026, 1, 1)})
    db_session.commit()

    resp = client.get("/protected-agent", headers=_hdr(raw))
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Agent token has been revoked"


def test_expired_token_rejected_with_historical_detail(
    db_session: Session, client: TestClient, seeded: tuple[str, str, str]
) -> None:
    raw, _, token_id = seeded
    db_session.query(AgentToken).filter_by(id=token_id).update({"expires_at": PAST})
    db_session.commit()

    resp = client.get("/protected-agent", headers=_hdr(raw))
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Agent token has expired"


def test_inactive_agent_rejected_with_historical_detail(
    db_session: Session, client: TestClient, seeded: tuple[str, str, str]
) -> None:
    raw, agent_id, _ = seeded
    db_session.query(Agent).filter_by(id=agent_id).update({"is_active": False})
    db_session.commit()

    resp = client.get("/protected-agent", headers=_hdr(raw))
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Agent not found or inactive"


# ── AC4: the touch COMMITS inside the service (timing change) ───────


def test_touch_commits_before_response(
    db_session: Session, client: TestClient, seeded: tuple[str, str, str]
) -> None:
    """The rewritten dependency stamps last_used_at via the service's
    commit-before-response invariant — not flush() + teardown-commit
    (the teardown never commits in this fixture, so a flush-only
    implementation would record zero commits here)."""
    raw, _, token_id = seeded

    with patch.object(db_session, "commit", wraps=db_session.commit) as commit_spy:
        resp = client.get("/protected-agent", headers=_hdr(raw))

    assert resp.status_code == 200, resp.text
    assert commit_spy.call_count == 1, (
        f"service touch must COMMIT during the request, commits={commit_spy.call_count}"
    )
    stored = db_session.get(AgentToken, token_id)
    assert stored is not None and stored.last_used_at is not None
