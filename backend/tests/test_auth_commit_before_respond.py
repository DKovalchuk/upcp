"""Regression: auth mutations must be committed BEFORE the endpoint returns.

Production `get_session` commits in the yield-teardown, which runs AFTER the
response is sent — so flush-only auth mutations race with the client's very
next request (observed in TASK-0142: immediate POST /auth/refresh after login
→ 401; probe: 2/40 refresh_token rows invisible at response receipt).

Each test uses a file-backed SQLite with two independent connections:
session A mimics the request session (teardown not yet run), connection B
mimics the client's next request arriving immediately after the response.
"""

from __future__ import annotations

import hashlib
from collections.abc import Generator
from pathlib import Path

import bcrypt
import pytest
from app.identity.models import User
from app.identity.service import AuthService
from app.identity.token_service import TokenService
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

SECRET = "test-secret-auth-commit"
EMAIL = "commit-probe@example.com"
PASSWORD = "CommitProbe123!"


@pytest.fixture()
def db_pair(tmp_path: Path) -> Generator[tuple[Engine, Engine], None, None]:
    """Two engines (=> two real connections) over the same SQLite file."""
    url = f"sqlite:///{tmp_path}/auth_commit.db"
    engine_a = create_engine(url)
    engine_b = create_engine(url)
    from app.shared.database import Base

    Base.metadata.create_all(bind=engine_a)
    yield engine_a, engine_b
    engine_a.dispose()
    engine_b.dispose()


def _seed_user(engine_a: Engine) -> str:
    with Session(engine_a) as s:
        user = User(
            email=EMAIL,
            password_hash=bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=12)).decode(),
            display_name="Commit Probe",
            is_active=True,
        )
        s.add(user)
        s.commit()
        return user.id


def _make_service(session: Session) -> AuthService:
    return AuthService(session, TokenService(secret_key=SECRET))


def _token(result: dict[str, object]) -> str:
    return str(result["refresh_token"])


def _refresh_visible(engine_b: Engine, raw_token: str) -> bool:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    with engine_b.connect() as conn:
        row = conn.execute(
            text("SELECT 1 FROM refresh_token WHERE token_hash = :h"),
            {"h": token_hash},
        ).fetchone()
    return row is not None


def test_login_persists_refresh_token_before_response(db_pair: tuple[Engine, Engine]) -> None:
    engine_a, engine_b = db_pair
    _seed_user(engine_a)
    session_a = Session(engine_a, expire_on_commit=False)

    result = _make_service(session_a).login(EMAIL, PASSWORD)

    assert _refresh_visible(engine_b, _token(result)), (
        "login response was built while the refresh_token row is still "
        "uncommitted — the client's immediate /auth/refresh will 401"
    )
    session_a.close()


def test_setup_persists_refresh_token_before_response(db_pair: tuple[Engine, Engine]) -> None:
    engine_a, engine_b = db_pair
    session_a = Session(engine_a, expire_on_commit=False)

    result = _make_service(session_a).setup(EMAIL, PASSWORD, "First Admin")

    assert _refresh_visible(engine_b, _token(result))
    session_a.close()


def test_refresh_rotation_persists_new_token_before_response(
    db_pair: tuple[Engine, Engine],
) -> None:
    engine_a, engine_b = db_pair
    _seed_user(engine_a)
    session_a = Session(engine_a, expire_on_commit=False)

    old_token = _token(_make_service(session_a).login(EMAIL, PASSWORD))
    session_a.commit()  # login persisted (its own commit / prior-request teardown)

    rotated = _make_service(session_a).refresh(old_token)

    assert _refresh_visible(engine_b, _token(rotated)), (
        "rotated refresh token must be committed before the response — "
        "otherwise the next refresh with it fails"
    )
    session_a.close()


def test_logout_revocation_visible_before_response(db_pair: tuple[Engine, Engine]) -> None:
    engine_a, engine_b = db_pair
    user_id = _seed_user(engine_a)
    session_a = Session(engine_a, expire_on_commit=False)

    login = _make_service(session_a).login(EMAIL, PASSWORD)
    raw = str(login["refresh_token"])
    access = str(login["access_token"])
    session_a.commit()
    _make_service(session_a).logout(raw, user_id, access)

    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    with engine_b.connect() as conn:
        row = conn.execute(
            text("SELECT revoked_at FROM refresh_token WHERE token_hash = :h"),
            {"h": token_hash},
        ).fetchone()
    assert row is not None and row[0] is not None, (
        "logout must commit the revocation before responding — otherwise a "
        "reused refresh token keeps working until the teardown lands"
    )
    session_a.close()


def test_change_password_persists_before_response(db_pair: tuple[Engine, Engine]) -> None:
    engine_a, engine_b = db_pair
    user_id = _seed_user(engine_a)
    session_a = Session(engine_a, expire_on_commit=False)

    new_password = "NewCommitPass456!"
    _make_service(session_a).change_password(user_id, PASSWORD, new_password)

    with engine_b.connect() as conn:
        stored = conn.execute(
            text("SELECT password_hash FROM user_account WHERE id = :id"),
            {"id": user_id},
        ).fetchone()
    assert stored is not None
    assert bcrypt.checkpw(new_password.encode(), stored[0].encode()), (
        "password change must be committed before responding — a login "
        "arriving right after would still see the old hash"
    )
    assert not bcrypt.checkpw(PASSWORD.encode(), stored[0].encode())
    session_a.close()
