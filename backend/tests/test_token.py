"""Tests for JWT token service.

TDD: Failing tests that define expected behavior.
"""

from datetime import timedelta

import pytest
from app.identity.models import RefreshToken, User
from app.identity.token_service import TokenService
from sqlalchemy.orm import Session


@pytest.fixture()
def token_service() -> TokenService:
    return TokenService()


@pytest.fixture()
def test_user(db_session: Session) -> User:
    user = User(
        email="token-test@example.com",
        password_hash="hash",
        display_name="Token Test",
    )
    db_session.add(user)
    db_session.flush()
    return user


# ---------------------------------------------------------------------------
# Access tokens
# ---------------------------------------------------------------------------


class TestAccessToken:
    def test_create_access_token_returns_string(
        self, token_service: TokenService, test_user: User
    ) -> None:
        token = token_service.create_access_token(test_user.id)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_access_token_contains_correct_payload(
        self, token_service: TokenService, test_user: User
    ) -> None:
        token = token_service.create_access_token(test_user.id)
        payload = token_service.verify_access_token(token)
        assert payload["sub"] == test_user.id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_access_token_custom_expiry(self, token_service: TokenService, test_user: User) -> None:
        token = token_service.create_access_token(test_user.id, expires_delta=timedelta(seconds=60))
        payload = token_service.verify_access_token(token)
        assert payload["sub"] == test_user.id

    def test_verify_access_token_valid(self, token_service: TokenService, test_user: User) -> None:
        token = token_service.create_access_token(test_user.id)
        payload = token_service.verify_access_token(token)
        assert payload["sub"] == test_user.id

    def test_verify_access_token_expired(
        self, token_service: TokenService, test_user: User
    ) -> None:
        token = token_service.create_access_token(test_user.id, expires_delta=timedelta(seconds=-1))
        with pytest.raises(ValueError, match="expired"):
            token_service.verify_access_token(token)

    def test_verify_access_token_invalid_signature(
        self, token_service: TokenService, test_user: User
    ) -> None:
        token = token_service.create_access_token(test_user.id)
        # Tamper with token
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(ValueError, match="Invalid token"):
            token_service.verify_access_token(tampered)

    def test_verify_refresh_token_as_access_rejected(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        refresh_token = token_service.create_refresh_token(test_user.id, db_session)
        with pytest.raises(ValueError, match="Invalid token"):
            token_service.verify_access_token(refresh_token)


# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------


class TestRefreshToken:
    def test_create_refresh_token_returns_string(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        token = token_service.create_refresh_token(test_user.id, db_session)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_refresh_token_stores_hash(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        token_service.create_refresh_token(test_user.id, db_session)
        stored = db_session.query(RefreshToken).first()
        assert stored is not None
        assert stored.user_id == test_user.id
        assert stored.token_hash is not None
        assert len(stored.token_hash) == 64  # SHA-256 hex

    def test_verify_refresh_token_valid(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        token = token_service.create_refresh_token(test_user.id, db_session)
        record = token_service.verify_refresh_token(token, db_session)
        assert record.user_id == test_user.id
        assert record.revoked_at is None

    def test_verify_refresh_token_expired(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        # Create token with past expiry by directly inserting
        import hashlib
        from datetime import UTC, datetime

        raw_token = "expired-token-value"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        record = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db_session.add(record)
        db_session.flush()

        with pytest.raises(ValueError, match="expired"):
            token_service.verify_refresh_token(raw_token, db_session)

    def test_verify_refresh_token_revoked(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        token = token_service.create_refresh_token(test_user.id, db_session)
        token_service.revoke_refresh_token(token, db_session)

        with pytest.raises(ValueError, match="revoked"):
            token_service.verify_refresh_token(token, db_session)

    def test_verify_refresh_token_not_found(
        self, token_service: TokenService, db_session: Session
    ) -> None:
        with pytest.raises(ValueError, match="not found"):
            token_service.verify_refresh_token("nonexistent-token", db_session)


# ---------------------------------------------------------------------------
# Token rotation
# ---------------------------------------------------------------------------


class TestTokenRotation:
    def test_rotate_refresh_token_returns_new_token(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        old_token = token_service.create_refresh_token(test_user.id, db_session)
        new_token = token_service.rotate_refresh_token(old_token, db_session)
        assert new_token != old_token
        assert isinstance(new_token, str)

    def test_rotate_invalidates_old_token(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        old_token = token_service.create_refresh_token(test_user.id, db_session)
        token_service.rotate_refresh_token(old_token, db_session)

        with pytest.raises(ValueError, match="revoked"):
            token_service.verify_refresh_token(old_token, db_session)

    def test_rotate_creates_new_valid_token(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        old_token = token_service.create_refresh_token(test_user.id, db_session)
        new_token = token_service.rotate_refresh_token(old_token, db_session)

        record = token_service.verify_refresh_token(new_token, db_session)
        assert record.user_id == test_user.id
        assert record.revoked_at is None

    def test_rotate_already_revoked_raises(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        old_token = token_service.create_refresh_token(test_user.id, db_session)
        token_service.revoke_refresh_token(old_token, db_session)

        with pytest.raises(ValueError, match="revoked"):
            token_service.rotate_refresh_token(old_token, db_session)

    def test_rotate_nonexistent_raises(
        self, token_service: TokenService, db_session: Session
    ) -> None:
        with pytest.raises(ValueError, match="not found"):
            token_service.rotate_refresh_token("nonexistent", db_session)


# ---------------------------------------------------------------------------
# Token revocation
# ---------------------------------------------------------------------------


class TestTokenRevocation:
    def test_revoke_sets_revoked_at(
        self, token_service: TokenService, test_user: User, db_session: Session
    ) -> None:
        token = token_service.create_refresh_token(test_user.id, db_session)
        token_service.revoke_refresh_token(token, db_session)

        from app.identity.token_service import _hash_token

        token_hash = _hash_token(token)
        stored = db_session.query(RefreshToken).filter_by(token_hash=token_hash).one()
        assert stored.revoked_at is not None

    def test_revoke_nonexistent_raises(
        self, token_service: TokenService, db_session: Session
    ) -> None:
        with pytest.raises(ValueError, match="not found"):
            token_service.revoke_refresh_token("nonexistent", db_session)
