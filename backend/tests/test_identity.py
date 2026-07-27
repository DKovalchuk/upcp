"""Tests for identity models: User, Organization, Membership.

TDD: This file contains failing tests that define the expected behavior.
Implement models to make them pass.
"""

import pytest
from app.identity.models import Membership, Organization, User
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

    def test_organization_timestamp_is_utc(self, db_session: Session) -> None:
        org = Organization(name="Time Org", slug="time-org")
        db_session.add(org)
        db_session.flush()
        assert org.created_at is not None
        assert org.created_at.tzinfo is not None


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
