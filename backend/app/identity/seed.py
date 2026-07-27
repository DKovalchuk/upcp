"""Seed default roles and permissions."""

from sqlalchemy.orm import Session

from app.identity.rbac import Permission, Role, RolePermission

# (action, resource)
DEFAULT_PERMISSIONS = [
    ("create", "project"),
    ("read", "project"),
    ("update", "project"),
    ("delete", "project"),
    ("create", "component"),
    ("read", "component"),
    ("update", "component"),
    ("delete", "component"),
    ("create", "module"),
    ("read", "module"),
    ("update", "module"),
    ("delete", "module"),
    ("create", "feature"),
    ("read", "feature"),
    ("update", "feature"),
    ("delete", "feature"),
    ("create", "task"),
    ("read", "task"),
    ("update", "task"),
    ("delete", "task"),
    ("read", "agent"),
    ("manage", "agent"),
    ("manage", "user"),
]

# role_name → list of (action, resource)
ROLE_PERMISSIONS = {
    "Owner": [  # Full access
        ("create", "project"),
        ("read", "project"),
        ("update", "project"),
        ("delete", "project"),
        ("create", "component"),
        ("read", "component"),
        ("update", "component"),
        ("delete", "component"),
        ("create", "module"),
        ("read", "module"),
        ("update", "module"),
        ("delete", "module"),
        ("create", "feature"),
        ("read", "feature"),
        ("update", "feature"),
        ("delete", "feature"),
        ("create", "task"),
        ("read", "task"),
        ("update", "task"),
        ("delete", "task"),
        ("read", "agent"),
        ("manage", "agent"),
        ("manage", "user"),
    ],
    "Admin": [  # Everything except user management
        ("create", "project"),
        ("read", "project"),
        ("update", "project"),
        ("delete", "project"),
        ("create", "component"),
        ("read", "component"),
        ("update", "component"),
        ("delete", "component"),
        ("create", "module"),
        ("read", "module"),
        ("update", "module"),
        ("delete", "module"),
        ("create", "feature"),
        ("read", "feature"),
        ("update", "feature"),
        ("delete", "feature"),
        ("create", "task"),
        ("read", "task"),
        ("update", "task"),
        ("delete", "task"),
        ("read", "agent"),
        ("manage", "agent"),
    ],
    "Member": [  # CRUD on work items
        ("create", "component"),
        ("read", "component"),
        ("update", "component"),
        ("create", "module"),
        ("read", "module"),
        ("update", "module"),
        ("create", "feature"),
        ("read", "feature"),
        ("update", "feature"),
        ("create", "task"),
        ("read", "task"),
        ("update", "task"),
    ],
    "Viewer": [  # Read only
        ("read", "project"),
        ("read", "component"),
        ("read", "module"),
        ("read", "feature"),
        ("read", "task"),
    ],
}


def seed_roles(db: Session) -> None:
    """Seed default roles and permissions. Idempotent."""
    # Upsert permissions
    perm_map: dict[tuple[str, str], Permission] = {}
    for action, resource in DEFAULT_PERMISSIONS:
        existing = db.query(Permission).filter_by(action=action, resource=resource).first()
        if existing is None:
            perm = Permission(action=action, resource=resource)
            db.add(perm)
            db.flush()
            perm_map[(action, resource)] = perm
        else:
            perm_map[(action, resource)] = existing

    # Upsert roles and link permissions
    for role_name, perms in ROLE_PERMISSIONS.items():
        existing_role = db.query(Role).filter_by(name=role_name).first()
        if existing_role is None:
            scope = "global" if role_name in ("Owner", "Admin") else "org"
            role = Role(name=role_name, scope=scope)
            db.add(role)
            db.flush()
        else:
            role = existing_role

        # Link permissions
        for action, resource in perms:
            perm = perm_map[(action, resource)]
            existing_link = (
                db.query(RolePermission).filter_by(role_id=role.id, permission_id=perm.id).first()
            )
            if existing_link is None:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    db.flush()
