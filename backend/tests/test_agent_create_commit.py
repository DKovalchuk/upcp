"""Regression: agent mutations must be committed before the handler returns.

Production `get_session` commits in the yield-teardown, which runs AFTER
the response is sent — so flush-only handlers race with the client's next
request (observed in TASK-0143 CI: POST /api/v1/agents 201 → immediate
POST .../tokens → 404 "Agent not found" in gate job 3296; same class as
TASK-0140's create→use(id) races, fixed then for delivery/structure but
not for agents).

Handlers are called DIRECTLY (no HTTP, no teardown) with session A;
connection B mimics the client's next request arriving right after the
response. Mirror of tests/test_auth_commit_before_respond.py.
"""

from __future__ import annotations

import hashlib
from collections.abc import Generator
from pathlib import Path

import bcrypt
import pytest
from app.identity.agent_endpoints import (
    AgentCreate,
    AgentTokenCreate,
    create_agent,
    create_agent_token,
    revoke_agent_token,
)
from app.identity.dependencies import CurrentUser
from app.identity.models import User
from app.identity.token_service import TokenService
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

SECRET = "test-secret-agent-commit"
EMAIL = "agent-commit@example.com"
PASSWORD = "AgentCommit123!"


@pytest.fixture()
def db_pair(tmp_path: Path) -> Generator[tuple[Engine, Engine], None, None]:
    """Two engines (=> two real connections) over the same SQLite file."""
    url = f"sqlite:///{tmp_path}/agent_commit.db"
    engine_a = create_engine(url)
    engine_b = create_engine(url)
    from app.shared.database import Base

    Base.metadata.create_all(bind=engine_a)
    yield engine_a, engine_b
    engine_a.dispose()
    engine_b.dispose()


def _seed_user(engine_a: Engine) -> CurrentUser:
    with Session(engine_a) as s:
        user = User(
            email=EMAIL,
            password_hash=bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=12)).decode(),
            display_name="Agent Commit",
            is_active=True,
            is_superuser=True,
        )
        s.add(user)
        s.commit()
        # build while attached: attributes expire on commit and the session
        # closes here (detached access would raise, not test the race)
        return CurrentUser(
            user_id=user.id, email=user.email, is_superuser=user.is_superuser, org_id=None
        )


def _visible(engine_b: Engine, sql: str, params: dict) -> bool:
    with engine_b.connect() as conn:
        return conn.execute(text(sql), params).fetchone() is not None


def test_create_agent_visible_before_response(db_pair) -> None:
    engine_a, engine_b = db_pair
    cu = _seed_user(engine_a)
    session_a = Session(engine_a, expire_on_commit=False)

    result = create_agent(AgentCreate(name="probe-agent"), cu, session_a)

    assert _visible(engine_b, "SELECT 1 FROM agent WHERE id = :id", {"id": result["id"]}), (
        "agent row must be committed before the 201 response — otherwise the client's immediate POST .../tokens 404s"
    )
    session_a.close()


def test_create_agent_token_visible_before_response(db_pair) -> None:
    engine_a, engine_b = db_pair
    cu = _seed_user(engine_a)
    session_a = Session(engine_a, expire_on_commit=False)

    agent = create_agent(AgentCreate(name="token-probe"), cu, session_a)
    session_a.commit()  # agent persisted (its own commit after the fix / prior request)

    result = create_agent_token(agent["id"], AgentTokenCreate(name="t1"), cu, session_a)

    token_hash = hashlib.sha256(result["token"].encode()).hexdigest()
    assert _visible(
        engine_b,
        "SELECT 1 FROM agent_token WHERE token_hash = :h",
        {"h": token_hash},
    ), (
        "token row must be committed before the 201 response — otherwise immediate middleware lookup 401s"
    )
    session_a.close()


def test_revoke_agent_token_visible_before_response(db_pair) -> None:
    engine_a, engine_b = db_pair
    cu = _seed_user(engine_a)
    session_a = Session(engine_a, expire_on_commit=False)

    agent = create_agent(AgentCreate(name="revoke-probe"), cu, session_a)
    session_a.commit()
    create_agent_token(agent["id"], AgentTokenCreate(name="t2"), cu, session_a)
    session_a.commit()

    record_id = None
    with Session(engine_a) as lookup:
        record_id = lookup.execute(
            text("SELECT id FROM agent_token WHERE agent_id = :a"), {"a": agent["id"]}
        ).scalar_one()

    revoke_agent_token(record_id, cu, session_a)

    assert _visible(
        engine_b,
        "SELECT 1 FROM agent_token WHERE id = :id AND revoked_at IS NOT NULL",
        {"id": record_id},
    ), "revocation must be committed before the response — otherwise a reused token keeps working"
    session_a.close()


def test_hash_matches_handler_scheme() -> None:
    """Sanity: the test hashes tokens the same way the middleware does."""
    raw = "x" * 16
    assert hashlib.sha256(raw.encode()).hexdigest() == _hash_local(raw)


def _hash_local(token: str) -> str:
    from app.identity.agent_endpoints import _hash_token

    return _hash_token(token)


# token_service import kept exercised (parity with auth-commit suite)
def test_token_service_constructs() -> None:
    assert TokenService(secret_key=SECRET) is not None
