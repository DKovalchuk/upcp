# Re-exports from app.auth for backward compatibility.
from app.auth.models import (  # noqa: F401
    RBACPermission,
    RBACRole,
    RBACUser,
    role_permission,
    user_role,
)
from app.auth.service import get_current_user  # noqa: F401
