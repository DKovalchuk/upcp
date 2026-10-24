"""Auth service — business logic for authentication flows.

Commit invariant: every state-mutating success path commits explicitly
before returning. `get_session`'s teardown commit runs AFTER the response
is sent, so flush-only mutations race with the client's next request
(immediate /auth/refresh after login → 401 — TASK-0142).
"""

from datetime import UTC, datetime
from typing import cast

import bcrypt
from sqlalchemy.orm import Session

from app.identity.denylist import deny_access_token
from app.identity.models import LoginAudit, Membership, Organization, RefreshToken, User
from app.identity.token_service import ACCESS_TOKEN_EXPIRY, TokenService

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 30


class AuthService:
    def __init__(self, db: Session, token_service: TokenService) -> None:
        self._db = db
        self._tokens = token_service

    # ── Setup ──────────────────────────────────────────────────────

    def setup(self, email: str, password: str, display_name: str) -> dict[str, object]:
        """First-run setup: create owner + default org."""
        existing = self._db.query(User).first()
        if existing is not None:
            raise ValueError("SETUP_ALREADY_COMPLETED")

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

        user = User(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            is_active=True,
            is_superuser=True,
            email_verified=True,
        )
        self._db.add(user)
        self._db.flush()

        org = Organization(
            name=f"{display_name}'s Organization",
            slug=display_name.lower().replace(" ", "-"),
            is_default=True,
        )
        self._db.add(org)
        self._db.flush()

        # Seed default roles
        from app.identity.rbac import Role, RoleBinding

        owner_role = Role(name="Owner", scope="global")
        self._db.add(owner_role)
        self._db.flush()

        binding = RoleBinding(user_id=user.id, role_id=owner_role.id)
        self._db.add(binding)
        self._db.flush()

        # Seed all default roles and permissions
        from app.identity.seed import seed_roles

        seed_roles(self._db)

        access = self._tokens.create_access_token(user.id)
        refresh = self._tokens.create_refresh_token(user.id, self._db)

        self._log_audit(user.id, email, "login_success")
        # commit before respond — teardown runs after the response (TASK-0142)
        self._db.commit()

        return {
            "user": {"id": user.id, "email": user.email, "display_name": user.display_name},
            "organization": {"id": org.id, "name": org.name, "slug": org.slug},
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        }

    # ── Login ──────────────────────────────────────────────────────

    def login(self, email: str, password: str, ip_address: str | None = None) -> dict[str, object]:
        """Authenticate user, return JWT pair."""
        user = self._db.query(User).filter_by(email=email).first()

        # Constant-time: always hash even if user not found
        if user is None:
            bcrypt.hashpw(b"dummy", bcrypt.gensalt())
            self._log_audit(None, email, "login_failed", ip_address)
            raise ValueError("INVALID_CREDENTIALS")

        if not user.is_active:
            self._log_audit(user.id, email, "login_failed", ip_address)
            raise ValueError("INVALID_CREDENTIALS")

        # Check lockout
        if user.locked_until is not None:
            if user.locked_until > datetime.now(UTC):
                self._log_audit(user.id, email, "login_failed", ip_address)
                raise ValueError("ACCOUNT_LOCKED")
            else:
                user.failed_login_attempts = 0
                user.locked_until = None

        # Verify password
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                from datetime import timedelta

                user.locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_MINUTES)
                self._log_audit(user.id, email, "account_locked", ip_address)
            self._db.flush()
            self._log_audit(user.id, email, "login_failed", ip_address)
            raise ValueError("INVALID_CREDENTIALS")

        # Success
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        self._db.flush()

        access = self._tokens.create_access_token(user.id)
        refresh = self._tokens.create_refresh_token(user.id, self._db)

        self._log_audit(user.id, email, "login_success", ip_address)
        # commit before respond — teardown runs after the response (TASK-0142)
        self._db.commit()

        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        }

    # ── Logout ─────────────────────────────────────────────────────

    def logout(self, refresh_token: str, user_id: str, access_token: str) -> None:
        """Revoke refresh token + denylist the access token (SPEC-0027 §3.3).

        The denylist entry self-expires with the token (TTL = exp − now);
        a Redis failure degrades best-effort — refresh revocation and
        audit still commit.
        """
        self._tokens.revoke_refresh_token(refresh_token, self._db)
        deny_access_token(access_token, self._access_ttl(access_token))
        self._log_audit(user_id, "", "logout")
        # commit before respond — teardown runs after the response (TASK-0142)
        self._db.commit()

    def _access_ttl(self, access_token: str) -> int:
        """Remaining access-token lifetime: exp − now, at least 1 second."""
        try:
            payload = self._tokens.verify_access_token(access_token)
            exp = int(cast(int | float, payload["exp"]))
        except (KeyError, TypeError, ValueError):
            # unreachable via the endpoint (dependency verified it) — bounded default
            return int(ACCESS_TOKEN_EXPIRY.total_seconds())
        return max(exp - int(datetime.now(UTC).timestamp()), 1)

    # ── Refresh ────────────────────────────────────────────────────

    def refresh(self, refresh_token: str) -> dict[str, object]:
        """Rotate refresh token, return new JWT pair."""
        record = self._tokens.verify_refresh_token(refresh_token, self._db)
        new_refresh = self._tokens.rotate_refresh_token(refresh_token, self._db)
        access = self._tokens.create_access_token(record.user_id)
        # commit before respond — teardown runs after the response (TASK-0142)
        self._db.commit()

        return {
            "access_token": access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }

    # ── Me ─────────────────────────────────────────────────────────

    def get_me(self, user_id: str) -> dict[str, object]:
        """Get current user with org and memberships."""
        user = self._db.query(User).filter_by(id=user_id).first()
        if user is None:
            raise ValueError("USER_NOT_FOUND")

        memberships = self._db.query(Membership).filter_by(user_id=user_id).all()

        org_ids = [m.org_id for m in memberships]
        orgs = (
            self._db.query(Organization).filter(Organization.id.in_(org_ids)).all()
            if org_ids
            else []
        )
        org_map = {o.id: o for o in orgs}

        return {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "organizations": [
                {
                    "id": m.org_id,
                    "name": org_map[m.org_id].name if m.org_id in org_map else "",
                    "role": m.role,
                }
                for m in memberships
            ],
        }

    # ── Password change ────────────────────────────────────────────

    def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        """Change the password and revoke every refresh token (SPEC-0027 §3.4).

        Closes finding 4: the docs promised "all refresh tokens invalidated"
        — the hash swap alone left every issued refresh token rotating for
        up to 7 days. Revocation lands in the same commit; other sessions'
        access JWTs stay valid until exp (<=15 min — killing those earlier
        needs a jti claim; documented limitation in docs/security/auth-rbac.md).
        """
        user = self._db.query(User).filter_by(id=user_id).first()
        if user is None:
            raise ValueError("USER_NOT_FOUND")

        if not bcrypt.checkpw(current_password.encode(), user.password_hash.encode()):
            raise ValueError("INVALID_CURRENT_PASSWORD")

        user.password_hash = bcrypt.hashpw(
            new_password.encode(), bcrypt.gensalt(rounds=12)
        ).decode()
        user.password_changed_at = datetime.now(UTC)
        (
            self._db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .update({"revoked_at": datetime.now(UTC)}, synchronize_session=False)
        )
        # commit before respond — teardown runs after the response (TASK-0142)
        self._db.commit()

        self._log_audit(user_id, user.email, "password_change")

    # ── Audit ──────────────────────────────────────────────────────

    def _log_audit(
        self,
        user_id: str | None,
        email: str,
        action: str,
        ip_address: str | None = None,
    ) -> None:
        audit = LoginAudit(
            user_id=user_id,
            email=email,
            action=action,
            ip_address=ip_address,
        )
        self._db.add(audit)
        self._db.flush()
