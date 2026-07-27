"""Tests for RBAC models: Role, Permission, RoleBinding."""

import pytest
from app.identity.models import Organization, User
from app.identity.rbac import Permission, Role, RoleBinding, RolePermission
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Role model
# ---------------------------------------------------------------------------


class TestRoleModel:
    def test_role_creation(self, db_session: Session) -> None:
        role = Role(name="admin", scope="global")
        db_session.add(role)
        db_session.flush()

        assert role.id is not None
        assert role.name == "admin"
        assert role.scope == "global"
        assert role.created_at is not None

    def test_role_name_unique(self, db_session: Session) -> None:
        r1 = Role(name="admin", scope="global")
        r2 = Role(name="admin", scope="org")
        db_session.add(r1)
        db_session.flush()

        db_session.add(r2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_role_scope_check_constraint(self, db_session: Session) -> None:
        role = Role(name="bad", scope="invalid_scope")
        db_session.add(role)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_role_scope_values(self, db_session: Session) -> None:
        for scope in ("global", "org", "project"):
            role = Role(name=f"role-{scope}", scope=scope)
            db_session.add(role)
            db_session.flush()
            assert role.scope == scope


# ---------------------------------------------------------------------------
# Permission model
# ---------------------------------------------------------------------------


class TestPermissionModel:
    def test_permission_creation(self, db_session: Session) -> None:
        perm = Permission(action="create", resource="project")
        db_session.add(perm)
        db_session.flush()

        assert perm.id is not None
        assert perm.action == "create"
        assert perm.resource == "project"
        assert perm.created_at is not None

    def test_permission_unique_action_resource(self, db_session: Session) -> None:
        p1 = Permission(action="create", resource="project")
        p2 = Permission(action="create", resource="project")
        db_session.add(p1)
        db_session.flush()

        db_session.add(p2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_permission_different_resources_ok(self, db_session: Session) -> None:
        p1 = Permission(action="create", resource="project")
        p2 = Permission(action="create", resource="task")
        db_session.add_all([p1, p2])
        db_session.flush()
        assert p1.id != p2.id


# ---------------------------------------------------------------------------
# RolePermission association
# ---------------------------------------------------------------------------


class TestRolePermission:
    def test_role_permission_link(self, db_session: Session) -> None:
        role = Role(name="editor", scope="org")
        perm = Permission(action="update", resource="task")
        db_session.add_all([role, perm])
        db_session.flush()

        rp = RolePermission(role_id=role.id, permission_id=perm.id)
        db_session.add(rp)
        db_session.flush()

        assert rp.role_id == role.id
        assert rp.permission_id == perm.id

    def test_role_permission_unique(self, db_session: Session) -> None:
        role = Role(name="viewer", scope="org")
        perm = Permission(action="read", resource="project")
        db_session.add_all([role, perm])
        db_session.flush()

        rp1 = RolePermission(role_id=role.id, permission_id=perm.id)
        rp2 = RolePermission(role_id=role.id, permission_id=perm.id)
        db_session.add(rp1)
        db_session.flush()

        db_session.add(rp2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_role_can_have_multiple_permissions(self, db_session: Session) -> None:
        role = Role(name="admin", scope="global")
        p1 = Permission(action="create", resource="project")
        p2 = Permission(action="delete", resource="task")
        db_session.add_all([role, p1, p2])
        db_session.flush()

        db_session.add_all(
            [
                RolePermission(role_id=role.id, permission_id=p1.id),
                RolePermission(role_id=role.id, permission_id=p2.id),
            ]
        )
        db_session.flush()

        links = db_session.query(RolePermission).filter_by(role_id=role.id).all()
        assert len(links) == 2


# ---------------------------------------------------------------------------
# RoleBinding model
# ---------------------------------------------------------------------------


class TestRoleBindingModel:
    def test_role_binding_global(self, db_session: Session) -> None:
        user = User(email="rbac@example.com", password_hash="hash", display_name="RBAC")
        role = Role(name="owner", scope="global")
        db_session.add_all([user, role])
        db_session.flush()

        binding = RoleBinding(user_id=user.id, role_id=role.id)
        db_session.add(binding)
        db_session.flush()

        assert binding.id is not None
        assert binding.user_id == user.id
        assert binding.role_id == role.id
        assert binding.org_id is None
        assert binding.project_id is None
        assert binding.created_at is not None

    def test_role_binding_org_scoped(self, db_session: Session) -> None:
        user = User(email="orgrbac@example.com", password_hash="hash", display_name="Org")
        org = Organization(name="Test Org", slug="test-org-rbac")
        role = Role(name="member", scope="org")
        db_session.add_all([user, org, role])
        db_session.flush()

        binding = RoleBinding(user_id=user.id, role_id=role.id, org_id=org.id)
        db_session.add(binding)
        db_session.flush()

        assert binding.org_id == org.id

    def test_role_binding_unique_user_role_org(self, db_session: Session) -> None:
        user = User(email="duprbac@example.com", password_hash="hash", display_name="Dup")
        org = Organization(name="Dup Org", slug="dup-org-rbac")
        role = Role(name="admin", scope="org")
        db_session.add_all([user, org, role])
        db_session.flush()

        b1 = RoleBinding(user_id=user.id, role_id=role.id, org_id=org.id)
        b2 = RoleBinding(user_id=user.id, role_id=role.id, org_id=org.id)
        db_session.add(b1)
        db_session.flush()

        db_session.add(b2)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_role_binding_cascade_on_user_delete(self, db_session: Session) -> None:
        user = User(email="cascade@example.com", password_hash="hash", display_name="Casc")
        role = Role(name="temp", scope="global")
        db_session.add_all([user, role])
        db_session.flush()

        binding = RoleBinding(user_id=user.id, role_id=role.id)
        db_session.add(binding)
        db_session.flush()

        db_session.delete(user)
        db_session.flush()

        remaining = db_session.query(RoleBinding).all()
        assert len(remaining) == 0
