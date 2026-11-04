"""FastAPI auth dependencies — JWT + agent token.

Agent token verification is implemented in agent_auth.py.
This module re-exports get_current_agent for backward compatibility.

TASK-0175 (SPEC-0029 §3.5): get_current_user reads subject state through
the cached ``SubjectStateService`` and the profile through
``UserRepository`` — no raw subject query in this presentation module.
"""

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

# Re-export from the actual implementation
from app.identity.agent_auth import get_current_agent  # noqa: F401
from app.identity.cache_provider import AuthCacheProvider
from app.identity.denylist import is_token_denied, note_denied_token
from app.identity.dependencies import CurrentAgent, CurrentUser  # noqa: F401
from app.identity.repositories import UserRepository
from app.identity.subject_state import SubjectStateService
from app.identity.token_service import TokenService
from app.shared.database import get_session


def _get_token_service() -> TokenService:
    return TokenService()


def _get_subject_state_service() -> SubjectStateService:
    """Liveness lookup for ``get_current_user`` (SPEC-0029 §3.3 / TASK-0175).

    Session split (documented): the service runs on SESSION-LESS
    repositories (its own lazy session per call) plus the cache provider,
    so the cached subject check adds no session to the request scope.
    The profile read in ``get_current_user`` reuses the request ``db``
    instead — ONE direct repository read per valid request: the cache
    serves the LIVENESS path (reject path + second call), not the
    profile. Recorded design decision in the TASK-0175 evidence.
    """
    return SubjectStateService(UserRepository(), AuthCacheProvider())


def _extract_bearer_token(authorization: str | None = Header(None)) -> str | None:
    """Extract token from Authorization: Bearer <token> header."""
    if authorization is None:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def get_current_user(
    request: Request,
    token: str | None = Depends(_extract_bearer_token),
    db: Session = Depends(get_session),
    token_service: TokenService = Depends(_get_token_service),
    subject_state: SubjectStateService = Depends(_get_subject_state_service),
) -> CurrentUser:
    """Validate JWT and return current user. Raises 401 on failure.

    Memo reuse (SPEC-0028 review FIX 6, ``agent_auth`` pattern): when the
    ``web_auth`` blanket already verified THIS exact token for this request
    (signature + denylist), its payload is reused — one verification per
    request through blanket + handler dependency. Standalone mounts without
    the blanket see no memo and run the full path below. Liveness and the
    profile read always run (per-request state).
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    memo_token = getattr(request.state, "verified_token", None)
    memo_payload = getattr(request.state, "verified_token_payload", None)
    if memo_token == token and isinstance(memo_payload, dict):
        payload = memo_payload  # blanket already verified + denylist-checked it
    else:
        try:
            payload = token_service.verify_access_token(token)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

        # SPEC-0027 §3.3: logout-denylisted tokens are dead (finding 3)
        if is_token_denied(token):
            note_denied_token(token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user_id: str = payload["sub"]

    # Liveness via the cached subject-state service (single point of
    # truth, SPEC-0028 web_auth): a valid signature does not imply a
    # live account — defense in depth under finding 2 / TASK-0146.
    # The reject path stops here; only "active" subjects pay for the
    # profile read below (cache serves liveness, not the profile).
    state = subject_state.get(user_id)
    user = UserRepository(db).get_by_id(user_id) if state == "active" else None
    if state != "active" or user is None:  # row gone within the cache TTL window
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
