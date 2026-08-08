"""FastAPI auth dependencies — JWT + agent token.

Agent token verification is implemented in agent_auth.py.
This module re-exports get_current_agent for backward compatibility.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

# Re-export from the actual implementation
from app.identity.agent_auth import get_current_agent  # noqa: F401
from app.identity.dependencies import CurrentAgent, CurrentUser  # noqa: F401
from app.identity.models import User
from app.identity.token_service import TokenService
from app.shared.database import get_session


def _get_token_service() -> TokenService:
    return TokenService()


def _extract_bearer_token(authorization: str | None = Header(None)) -> str | None:
    """Extract token from Authorization: Bearer <token> header."""
    if authorization is None:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def get_current_user(
    token: str | None = Depends(_extract_bearer_token),
    db: Session = Depends(get_session),
    token_service: TokenService = Depends(_get_token_service),
) -> CurrentUser:
    """Validate JWT and return current user. Raises 401 on failure."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = token_service.verify_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user_id: str = payload["sub"]  # type: ignore[assignment]
    user = db.query(User).filter_by(id=user_id).first()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        user_id=user.id,
        email=user.email,
        is_superuser=user.is_superuser,
    )
