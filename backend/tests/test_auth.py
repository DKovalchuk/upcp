from app.auth.models import RBACPermission, RBACRole, RBACUser
from app.auth.service import get_current_user


def test_user_model_has_expected_columns() -> None:
    cols = {c.name for c in RBACUser.__table__.columns}
    assert "id" in cols
    assert "username" in cols
    assert "email" in cols
    assert "is_active" in cols
    assert "created_at" in cols


def test_role_model_has_expected_columns() -> None:
    cols = {c.name for c in RBACRole.__table__.columns}
    assert "id" in cols
    assert "name" in cols


def test_permission_model_has_expected_columns() -> None:
    cols = {c.name for c in RBACPermission.__table__.columns}
    assert "id" in cols
    assert "name" in cols


def test_get_current_user_returns_placeholder() -> None:
    user = get_current_user()
    assert user.username == "admin"
    assert user.email == "admin@upcp.local"
    assert user.is_active is True


def test_user_role_association_exists() -> None:
    from app.auth.models import user_role

    assert user_role.name == "user_role"


def test_role_permission_association_exists() -> None:
    from app.auth.models import role_permission

    assert role_permission.name == "role_permission"
