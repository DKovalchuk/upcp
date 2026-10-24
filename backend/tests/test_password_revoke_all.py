"""Password change revokes ALL refresh tokens — SPEC-0027 §3.4 / TASK-0148 (red → green).

Finding 4 (code half): docs promised "invalidates all of the user's
refresh tokens" on password change; the code only swapped the hash, so
every previously issued refresh token kept rotating (7-day window).
Red first: both rotations below succeed today — green after
``change_password`` revokes every refresh row in the same commit.

Other sessions' access JWTs remain valid until exp — documented
limitation (AC2), not asserted here (needs a jti claim to enforce).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.identity.models import LoginAudit, RefreshToken, User
from app.identity.service import AuthService
from app.identity.token_service import TokenService
from sqlalchemy.orm import Session

SECRET = "test-secret-password-revoke"
OLD_PASSWORD = "OldPassword123!"
NEW_PASSWORD = "NewPassword456!"


def _purge(db: Session, user_id: str) -> None:
    """change_password commits (audit invariant) — remove the rows so later
    files that assume an empty user table stay order-independent."""
    db.query(RefreshToken).filter_by(user_id=user_id).delete()
    db.query(LoginAudit).filter_by(user_id=user_id).delete()
    db.query(User).filter_by(id=user_id).delete()
    db.commit()


@pytest.fixture()
def subject(db_session: Session) -> str:
    import bcrypt

    email = f"pw-revoke-{uuid4().hex[:10]}@example.com"
    user = User(
        email=email,
        password_hash=bcrypt.hashpw(OLD_PASSWORD.encode(), bcrypt.gensalt(rounds=12)).decode(),
        display_name="PwRevoke",
    )
    db_session.add(user)
    db_session.flush()
    user_id = str(user.id)
    yield user_id
    _purge(db_session, user_id)


def test_password_change_revokes_all_refresh_tokens(db_session: Session, subject: str) -> None:
    """AC1: after change_password every old refresh token is dead (rotate → 401)."""
    ts = TokenService(secret_key=SECRET)
    raw_first = ts.create_refresh_token(subject, db_session)
    raw_second = ts.create_refresh_token(subject, db_session)
    db_session.commit()

    # sanity: both are live before the password change
    assert ts.verify_refresh_token(raw_first, db_session) is not None
    assert ts.verify_refresh_token(raw_second, db_session) is not None

    service = AuthService(db_session, ts)
    service.change_password(subject, OLD_PASSWORD, NEW_PASSWORD)

    # same call chain as POST /auth/refresh: verify_refresh_token
    # → ValueError → endpoint 401
    for raw in (raw_first, raw_second):
        with pytest.raises(ValueError, match="revoked"):
            ts.verify_refresh_token(raw, db_session)


def test_password_change_still_requires_correct_current_password(
    db_session: Session, subject: str
) -> None:
    """Negative guard: no revocation when the change is refused (400 path)."""
    ts = TokenService(secret_key=SECRET)
    raw = ts.create_refresh_token(subject, db_session)
    db_session.commit()

    service = AuthService(db_session, ts)
    with pytest.raises(ValueError, match="INVALID_CURRENT_PASSWORD"):
        service.change_password(subject, "WrongCurrent999!", NEW_PASSWORD)

    assert ts.verify_refresh_token(raw, db_session) is not None, (
        "a refused password change must not revoke anything"
    )
