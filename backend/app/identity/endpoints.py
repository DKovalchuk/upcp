"""Auth API endpoints — setup, login, logout, refresh, me, password change."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.identity.auth import _get_token_service, get_current_user
from app.identity.dependencies import CurrentUser
from app.identity.service import AuthService
from app.identity.token_service import TokenService
from app.shared.database import get_session

router = APIRouter(tags=["auth"])


def _get_auth_service(
    db: Session = Depends(get_session),
    token_service: TokenService = Depends(_get_token_service),
) -> AuthService:
    return AuthService(db, token_service)


# ── Schemas ───────────────────────────────────────────────────────


class SetupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Endpoints ─────────────────────────────────────────────────────


@router.post("/setup", status_code=status.HTTP_201_CREATED)
def auth_setup(
    body: SetupRequest,
    auth: AuthService = Depends(_get_auth_service),
) -> dict[str, object]:
    try:
        return auth.setup(body.email, body.password, body.display_name)
    except ValueError as e:
        if str(e) == "SETUP_ALREADY_COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Setup has already been completed",
            ) from None
        raise


@router.post("/login", response_model=TokenResponse)
def auth_login(
    body: LoginRequest,
    request: Request,
    auth: AuthService = Depends(_get_auth_service),
) -> dict[str, object]:
    ip = request.client.host if request.client else None
    try:
        return auth.login(body.email, body.password, ip_address=ip)
    except ValueError as e:
        if str(e) == "ACCOUNT_LOCKED":
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed attempts",
            ) from None
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from None


@router.post("/logout")
def auth_logout(
    body: RefreshRequest,
    user: CurrentUser = Depends(get_current_user),
    auth: AuthService = Depends(_get_auth_service),
) -> dict[str, object]:
    auth.logout(body.refresh_token, user.user_id)
    return {"ok": True}


@router.post("/refresh", response_model=TokenResponse)
def auth_refresh(
    body: RefreshRequest,
    auth: AuthService = Depends(_get_auth_service),
) -> dict[str, object]:
    try:
        return auth.refresh(body.refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from None


@router.get("/me")
def auth_me(
    user: CurrentUser = Depends(get_current_user),
    auth: AuthService = Depends(_get_auth_service),
) -> dict[str, object]:
    try:
        return auth.get_me(user.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from None


@router.post("/password/change")
def auth_password_change(
    body: PasswordChangeRequest,
    user: CurrentUser = Depends(get_current_user),
    auth: AuthService = Depends(_get_auth_service),
) -> dict[str, object]:
    try:
        auth.change_password(user.user_id, body.current_password, body.new_password)
        return {"ok": True}
    except ValueError as e:
        if str(e) == "INVALID_CURRENT_PASSWORD":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            ) from None
        raise
