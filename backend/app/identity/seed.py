"""Seed default roles and permissions."""

from sqlalchemy.orm import Session

from app.identity.rbac import Permission, Role, RolePermission

# (action, resource)
# Phase-B pairs (TASK-0172): dangerous mutations outside the Phase-A CRUD —
# subtask deletes, quality gates (AC/DoD), evidence/review decisions and
# integration config (notification channels, git providers/links).
# Referenced by route gates; see tasks/TASK-0172-rbac-coverage.md inventory.
PHASE_B_ADMIN_PERMISSIONS = [
    ("delete", "subtask"),
    ("create", "acceptance_criteria"),
    ("update", "acceptance_criteria"),
    ("delete", "acceptance_criteria"),
    ("create", "dod_item"),
    ("update", "dod_item"),
    ("delete", "dod_item"),
    ("create", "evidence"),
    ("update", "evidence"),
    ("create", "review_round"),
    ("update", "review_round"),
    ("create", "review_finding"),
    ("create", "notification_channel"),
    ("update", "notification_channel"),
    ("delete", "notification_channel"),
    ("create", "git_provider"),
    ("update", "git_provider"),
    ("delete", "git_provider"),
    ("delete", "git_link"),
]

# Member keeps work-item create/update on quality entities, no deletes
# (mirrors Member's lack of delete:component/delete:task); integration
# config (channels, git) stays Owner/Admin — see the inventory table.
PHASE_B_MEMBER_PERMISSIONS = [
    ("create", "acceptance_criteria"),
    ("update", "acceptance_criteria"),
    ("create", "dod_item"),
    ("update", "dod_item"),
    ("create", "evidence"),
    ("update", "evidence"),
    ("create", "review_round"),
    ("update", "review_round"),
    ("create", "review_finding"),
]

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
    *PHASE_B_ADMIN_PERMISSIONS,
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
        *PHASE_B_ADMIN_PERMISSIONS,
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
        *PHASE_B_ADMIN_PERMISSIONS,
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
        *PHASE_B_MEMBER_PERMISSIONS,
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
