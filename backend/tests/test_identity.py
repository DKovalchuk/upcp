"""Tests for identity models: User, Organization, Membership, LoginAudit.

TDD: This file contains failing tests that define the expected behavior.
Implement models to make them pass.
"""

import pytest
from app.identity.models import LoginAudit, Membership, Organization, User
from app.identity.schemas import (
    OrganizationCreate,
    OrganizationRead,
    UserCreate,
    UserRead,
    UserReadAdmin,
)
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


class TestUserModel:
    def test_user_creation(self, db_session: Session) -> None:
        user = User(
            email="alice@example.com",
            password_hash="bcrypt$abc123",
            display_name="Alice",
        )
        db_session.add(user)
        db_session.flush()

        assert user.id is not None
        assert user.email == "alice@example.com"
        assert user.password_hash == "bcrypt$abc123"
        assert user.display_name == "Alice"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.email_verified is False
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        assert user.last_login_at is None
        assert user.password_changed_at is None
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_email_unique(self, db_session: Session) -> None:
        user1 = User(
            email="dup@example.com",
            password_hash="hash1",
            display_name="User 1",
        )
        user2 = User(
            email="dup@example.com",
            password_hash="hash2",
            display_name="User 2",
        )
        db_session.add(user1)
        db_session.flush()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_user_email_required(self, db_session: Session) -> None:
        user = User(
            email=None,  # type: ignore[arg-type]
            password_hash="hash",
            display_name="No Email",
        )
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_user_password_hash_not_raw(self, db_session: Session) -> None:
        raw_password = "supersecret123"
        user = User(
            email="secure@example.com",
            password_hash=f"bcrypt${raw_password}",
            display_name="Secure",
        )
        db_session.add(user)
        db_session.flush()

        assert user.password_hash != raw_password
        assert user.password_hash.startswith("bcrypt$")

    def test_user_is_active_default_true(self, db_session: Session) -> None:
        user = User(
            email="active@example.com",
            password_hash="hash",
            display_name="Active",
        )
        db_session.add(user)
        db_session.flush()
        assert user.is_active is True

    def test_user_is_superuser_default_false(self, db_session: Session) -> None:
        user = User(
            email="normal@example.com",
            password_hash="hash",
            display_name="Normal",
        )
        db_session.add(user)
        db_session.flush()
        assert user.is_superuser is False

    def test_user_email_verified_default_false(self, db_session: Session) -> None:
        user = User(
            email="unverified@example.com",
            password_hash="hash",
            display_name="Unverified",
        )
        db_session.add(user)
        db_session.flush()
        assert user.email_verified is False

    def test_user_security_fields_defaults(self, db_session: Session) -> None:
        user = User(
            email="security@example.com",
            password_hash="hash",
            display_name="Security",
        )
        db_session.add(user)
        db_session.flush()
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        assert user.last_login_at is None
        assert user.password_changed_at is None

    def test_user_query_by_email(self, db_session: Session) -> None:
        user = User(
            email="findme@example.com",
            password_hash="hash",
            display_name="Find Me",
        )
        db_session.add(user)
        db_session.flush()

        found = db_session.query(User).filter_by(email="findme@example.com").one()
        assert found.id == user.id

    def test_user_timestamps_are_utc(self, db_session: Session) -> None:
        user = User(
            email="time@example.com",
            password_hash="hash",
            display_name="Time",
        )
        db_session.add(user)
        db_session.flush()

        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at.tzinfo is not None


# ---------------------------------------------------------------------------
# Organization model
# ---------------------------------------------------------------------------


class TestOrganizationModel:
    def test_organization_creation(self, db_session: Session) -> None:
        org = Organization(name="Acme Corp", slug="acme-corp")
        db_session.add(org)
        db_session.flush()

        assert org.id is not None
        assert org.name == "Acme Corp"
        assert org.slug == "acme-corp"
        assert org.is_default is False
        assert org.created_at is not None
        assert org.updated_at is not None

    def test_organization_slug_unique(self, db_session: Session) -> None:
        org1 = Organization(name="Org 1", slug="same-slug")
        org2 = Organization(name="Org 2", slug="same-slug")
        db_session.add(org1)
        db_session.flush()

        db_session.add(org2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_organization_slug_required(self, db_session: Session) -> None:
        org = Organization(name="No Slug", slug=None)  # type: ignore[arg-type]
        db_session.add(org)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_organization_is_default_default_false(self, db_session: Session) -> None:
        org = Organization(name="Default Check", slug="default-check")
        db_session.add(org)
        db_session.flush()
        assert org.is_default is False

    def test_organization_timestamps_are_utc(self, db_session: Session) -> None:
        org = Organization(name="Time Org", slug="time-org")
        db_session.add(org)
        db_session.flush()
        assert org.created_at is not None
        assert org.created_at.tzinfo is not None
        assert org.updated_at is not None
        assert org.updated_at.tzinfo is not None


# ---------------------------------------------------------------------------
# Membership model
# ---------------------------------------------------------------------------


class TestMembershipModel:
    def test_membership_creation(self, db_session: Session) -> None:
        user = User(
            email="member@example.com",
            password_hash="hash",
            display_name="Member",
        )
        org = Organization(name="Test Org", slug="test-org")
        db_session.add_all([user, org])
        db_session.flush()

        membership = Membership(user_id=user.id, org_id=org.id, role="member")
        db_session.add(membership)
        db_session.flush()

        assert membership.id is not None
        assert membership.user_id == user.id
        assert membership.org_id == org.id
        assert membership.role == "member"
        assert membership.created_at is not None

    def test_membership_unique_user_org(self, db_session: Session) -> None:
        user = User(
            email="dup-member@example.com",
            password_hash="hash",
            display_name="Dup Member",
        )
        org = Organization(name="Dup Org", slug="dup-org")
        db_session.add_all([user, org])
        db_session.flush()

        m1 = Membership(user_id=user.id, org_id=org.id, role="member")
        m2 = Membership(user_id=user.id, org_id=org.id, role="admin")
        db_session.add(m1)
        db_session.flush()

        db_session.add(m2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_membership_role_check_constraint(self, db_session: Session) -> None:
        user = User(
            email="badrole@example.com",
            password_hash="hash",
            display_name="Bad Role",
        )
        org = Organization(name="Bad Role Org", slug="bad-role-org")
        db_session.add_all([user, org])
        db_session.flush()

        membership = Membership(user_id=user.id, org_id=org.id, role="superadmin")
        db_session.add(membership)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_membership_role_values(self, db_session: Session) -> None:
        org = Organization(name="Roles Org", slug="roles-org")
        db_session.add(org)
        db_session.flush()

        for i, role in enumerate(("owner", "admin", "member", "viewer")):
            user = User(
                email=f"role-{i}@example.com",
                password_hash="hash",
                display_name=f"Role {role}",
            )
            db_session.add(user)
            db_session.flush()

            membership = Membership(user_id=user.id, org_id=org.id, role=role)
            db_session.add(membership)
            db_session.flush()
            assert membership.role == role

    def test_membership_cascade_on_user_delete(self, db_session: Session) -> None:
        user = User(
            email="cascade@example.com",
            password_hash="hash",
            display_name="Cascade",
        )
        org = Organization(name="Cascade Org", slug="cascade-org")
        db_session.add_all([user, org])
        db_session.flush()

        membership = Membership(user_id=user.id, org_id=org.id, role="member")
        db_session.add(membership)
        db_session.flush()

        db_session.delete(user)
        db_session.flush()

        remaining = db_session.query(Membership).filter_by(org_id=org.id).all()
        assert len(remaining) == 0


# ---------------------------------------------------------------------------
# LoginAudit model
# ---------------------------------------------------------------------------


class TestLoginAuditModel:
    def test_login_audit_creation(self, db_session: Session) -> None:
        user = User(
            email="audit@example.com",
            password_hash="hash",
            display_name="Audit",
        )
        db_session.add(user)
        db_session.flush()

        audit = LoginAudit(
            user_id=user.id,
            email=user.email,
            action="login_success",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        db_session.add(audit)
        db_session.flush()

        assert audit.id is not None
        assert audit.user_id == user.id
        assert audit.email == "audit@example.com"
        assert audit.action == "login_success"
        assert audit.ip_address == "192.168.1.1"
        assert audit.user_agent == "Mozilla/5.0"
        assert audit.created_at is not None

    def test_login_audit_nullable_user_id(self, db_session: Session) -> None:
        """Failed login may not have a user_id (user not found)."""
        audit = LoginAudit(
            user_id=None,
            email="unknown@example.com",
            action="login_failed",
            ip_address="10.0.0.1",
        )
        db_session.add(audit)
        db_session.flush()

        assert audit.user_id is None
        assert audit.action == "login_failed"

    def test_login_audit_action_check_constraint(self, db_session: Session) -> None:
        audit = LoginAudit(
            email="bad@example.com",
            action="invalid_action",
        )
        db_session.add(audit)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_login_audit_valid_actions(self, db_session: Session) -> None:
        valid_actions = (
            "login_success",
            "login_failed",
            "logout",
            "password_change",
            "token_created",
            "token_revoked",
            "account_locked",
            "account_unlocked",
        )
        for action in valid_actions:
            audit = LoginAudit(
                email=f"{action}@example.com",
                action=action,
            )
            db_session.add(audit)
            db_session.flush()
            assert audit.action == action

    def test_login_audit_user_id_nullable(self, db_session: Session) -> None:
        """user_id is nullable — SET NULL on delete is configured in FK."""
        audit = LoginAudit(
            user_id=None,
            email="orphan@example.com",
            action="login_success",
        )
        db_session.add(audit)
        db_session.flush()
        assert audit.user_id is None


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class TestUserSchemas:
    def test_user_create_valid(self) -> None:
        user = UserCreate(
            email="test@example.com",
            password="securepass123",
            display_name="Test",
        )
        assert user.email == "test@example.com"
        assert user.password == "securepass123"

    def test_user_create_password_too_short(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="short",
                display_name="Test",
            )

    def test_user_create_password_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="x" * 129,
                display_name="Test",
            )

    def test_user_create_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                password="securepass123",
                display_name="Test",
            )

    def test_user_read_no_superuser_leak(self) -> None:
        data = {
            "id": "1",
            "email": "test@example.com",
            "display_name": "Test",
            "is_active": True,
            "email_verified": False,
            "last_login_at": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        user = UserRead.model_validate(data)
        assert not hasattr(user, "is_superuser")

    def test_user_read_admin_has_superuser(self) -> None:
        data = {
            "id": "1",
            "email": "admin@example.com",
            "display_name": "Admin",
            "is_active": True,
            "is_superuser": True,
            "email_verified": True,
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login_at": None,
            "password_changed_at": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        user = UserReadAdmin.model_validate(data)
        assert user.is_superuser is True
        assert user.failed_login_attempts == 0


class TestOrganizationSchemas:
    def test_organization_create_valid(self) -> None:
        org = OrganizationCreate(name="Acme", slug="acme")
        assert org.slug == "acme"

    def test_organization_create_invalid_slug(self) -> None:
        with pytest.raises(ValidationError):
            OrganizationCreate(name="Acme", slug="Acme Corp!")

    def test_organization_read_has_updated_at(self) -> None:
        data = {
            "id": "1",
            "name": "Acme",
            "slug": "acme",
            "is_default": False,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        org = OrganizationRead.model_validate(data)
        assert org.updated_at is not None
