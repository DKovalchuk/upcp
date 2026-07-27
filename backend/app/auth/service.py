from app.auth.models import RBACUser


def get_current_user() -> RBACUser:
    """Placeholder: returns a default admin user. Real auth added later."""
    return RBACUser(
        id="00000000-0000-0000-0000-000000000001",
        username="admin",
        email="admin@upcp.local",
        is_active=True,
    )
