"""JWT token service — access tokens (stateless) + refresh tokens (DB-stored)."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.orm import Session

from app.identity.models import RefreshToken
from app.shared.config import get_settings
from app.shared.text import new_id

settings = get_settings()

ACCESS_TOKEN_EXPIRY = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRY = timedelta(days=7)


def _hash_token(token: str) -> str:
    """SHA-256 hash of token for DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class TokenService:
    def __init__(self, secret_key: str | None = None) -> None:
        self._secret = secret_key or settings.secret_key
        self._algorithm = "HS256"

    # ── Access tokens ──────────────────────────────────────────────

    def create_access_token(
        self,
        user_id: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        now = datetime.now(UTC)
        expiry = expires_delta or ACCESS_TOKEN_EXPIRY
        payload = {
            "sub": user_id,
            "type": "access",
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + expiry,
        }
        return str(jwt.encode(payload, self._secret, algorithm=self._algorithm))

    def verify_access_token(self, token: str) -> dict[str, object]:
        try:
            payload: dict[str, object] = jwt.decode(
                token, self._secret, algorithms=[self._algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired") from None
        except jwt.InvalidSignatureError:
            raise ValueError("Invalid token signature") from None
        except jwt.DecodeError:
            raise ValueError("Invalid token") from None

        if payload.get("type") != "access":
            raise ValueError("Invalid token type — expected access token")

        return payload

    # ── Refresh tokens ─────────────────────────────────────────────

    def create_refresh_token(self, user_id: str, db: Session) -> str:
        """Create a refresh token, store its hash in DB, return raw token."""
        raw_token = secrets.token_urlsafe(48)
        token_hash = _hash_token(raw_token)
        now = datetime.now(UTC)

        record = RefreshToken(
            id=new_id(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=now + REFRESH_TOKEN_EXPIRY,
        )
        db.add(record)
        db.flush()
        return raw_token

    def verify_refresh_token(self, token: str, db: Session) -> RefreshToken:
        """Verify refresh token and return the DB record."""
        token_hash = _hash_token(token)
        record = db.query(RefreshToken).filter_by(token_hash=token_hash).first()

        if record is None:
            raise ValueError("Refresh token not found")

        if record.revoked_at is not None:
            raise ValueError("Refresh token has been revoked")

        # Handle both naive (SQLite) and aware (PostgreSQL) datetimes
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise ValueError("Refresh token has expired")

        return record

    def rotate_refresh_token(self, old_token: str, db: Session) -> str:
        """Rotate: revoke old, create new, return new raw token."""
        record = self.verify_refresh_token(old_token, db)

        # Revoke old
        record.revoked_at = datetime.now(UTC)

        # Create new
        new_raw = secrets.token_urlsafe(48)
        new_record = RefreshToken(
            id=new_id(),
            user_id=record.user_id,
            token_hash=_hash_token(new_raw),
            expires_at=datetime.now(UTC) + REFRESH_TOKEN_EXPIRY,
        )
        db.add(new_record)
        db.flush()

        return new_raw

    def revoke_refresh_token(self, token: str, db: Session) -> None:
        """Mark a refresh token as revoked."""
        token_hash = _hash_token(token)
        record = db.query(RefreshToken).filter_by(token_hash=token_hash).first()

        if record is None:
            raise ValueError("Refresh token not found")

        record.revoked_at = datetime.now(UTC)
        db.flush()
