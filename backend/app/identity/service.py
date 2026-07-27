"""Auth service — business logic for authentication flows."""

from datetime import UTC, datetime

import bcrypt
from sqlalchemy.orm import Session

from app.identity.models import LoginAudit, Membership, Organization, User
from app.identity.token_service import TokenService

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

        access = self._tokens.create_access_token(user.id)
        refresh = self._tokens.create_refresh_token(user.id, self._db)

        self._log_audit(user.id, email, "login_success")

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

        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        }

    # ── Logout ─────────────────────────────────────────────────────

    def logout(self, refresh_token: str, user_id: str) -> None:
        """Revoke refresh token."""
        self._tokens.revoke_refresh_token(refresh_token, self._db)
        self._log_audit(user_id, "", "logout")

    # ── Refresh ────────────────────────────────────────────────────

    def refresh(self, refresh_token: str) -> dict[str, object]:
        """Rotate refresh token, return new JWT pair."""
        record = self._tokens.verify_refresh_token(refresh_token, self._db)
        new_refresh = self._tokens.rotate_refresh_token(refresh_token, self._db)
        access = self._tokens.create_access_token(record.user_id)

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
        """Change user password."""
        user = self._db.query(User).filter_by(id=user_id).first()
        if user is None:
            raise ValueError("USER_NOT_FOUND")

        if not bcrypt.checkpw(current_password.encode(), user.password_hash.encode()):
            raise ValueError("INVALID_CURRENT_PASSWORD")

        user.password_hash = bcrypt.hashpw(
            new_password.encode(), bcrypt.gensalt(rounds=12)
        ).decode()
        user.password_changed_at = datetime.now(UTC)
        self._db.flush()

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
