"""Tests for RBAC seeding — default roles and permissions."""

from app.identity.rbac import Permission, Role, RolePermission
from app.identity.seed import seed_roles
from sqlalchemy.orm import Session


class TestSeedRoles:
    def test_seed_creates_roles(self, db_session: Session) -> None:
        seed_roles(db_session)

        roles = db_session.query(Role).all()
        names = {r.name for r in roles}
        assert "Owner" in names
        assert "Admin" in names
        assert "Member" in names
        assert "Viewer" in names

    def test_seed_creates_permissions(self, db_session: Session) -> None:
        seed_roles(db_session)

        perms = db_session.query(Permission).all()
        assert len(perms) > 0
        actions = {p.action for p in perms}
        assert "create" in actions
        assert "read" in actions
        assert "update" in actions
        assert "delete" in actions
        assert "manage" in actions

    def test_seed_creates_role_permission_links(self, db_session: Session) -> None:
        seed_roles(db_session)

        links = db_session.query(RolePermission).all()
        assert len(links) > 0

    def test_seed_idempotent(self, db_session: Session) -> None:
        seed_roles(db_session)
        seed_roles(db_session)

        roles = db_session.query(Role).all()
        # Should have exactly 4 roles, not 8
        assert len(roles) == 4

    def test_owner_has_all_permissions(self, db_session: Session) -> None:
        seed_roles(db_session)

        owner = db_session.query(Role).filter_by(name="Owner").one()
        links = db_session.query(RolePermission).filter_by(role_id=owner.id).all()
        # Owner should have permissions on all resources
        assert len(links) >= 10

    def test_viewer_has_read_only(self, db_session: Session) -> None:
        seed_roles(db_session)

        viewer = db_session.query(Role).filter_by(name="Viewer").one()
        links = (
            db_session.query(RolePermission)
            .join(Permission)
            .filter(RolePermission.role_id == viewer.id)
            .all()
        )
        perm_ids = [link.permission_id for link in links]
        perms = db_session.query(Permission).filter(Permission.id.in_(perm_ids)).all()
        actions = {p.action for p in perms}
        assert actions == {"read"}
