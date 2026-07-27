"""add identity models: user, organization, membership, login_audit

Revision ID: ebfcf69f5774
Revises: 0011
Create Date: 2026-07-27 13:59:49.097565

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ebfcf69f5774"
down_revision: str | Sequence[str] | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- organization ---
    op.create_table(
        "organization",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    # --- user_account ---
    op.create_table(
        "user_account",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # --- membership ---
    op.create_table(
        "membership",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("org_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "org_id"),
        sa.CheckConstraint(
            "role IN ('owner', 'admin', 'member', 'viewer')",
            name="ck_membership_role",
        ),
    )
    op.create_index("ix_membership_user_id", "membership", ["user_id"])
    op.create_index("ix_membership_org_id", "membership", ["org_id"])
    op.create_index("ix_membership_org_user", "membership", ["org_id", "user_id"])

    # --- login_audit ---
    op.create_table(
        "login_audit",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "action IN ('login_success', 'login_failed', 'logout', "
            "'password_change', 'token_created', 'token_revoked', "
            "'account_locked', 'account_unlocked')",
            name="ck_login_audit_action",
        ),
    )
    op.create_index("ix_login_audit_user_id", "login_audit", ["user_id"])
    op.create_index("ix_login_audit_action", "login_audit", ["action"])
    op.create_index("ix_login_audit_created_at", "login_audit", ["created_at"])

    # --- refresh_token ---
    op.create_table(
        "refresh_token",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_refresh_token_user_id", "refresh_token", ["user_id"])
    op.create_index("ix_refresh_token_token_hash", "refresh_token", ["token_hash"], unique=True)

    # --- iam_role ---
    op.create_table(
        "iam_role",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.CheckConstraint("scope IN ('global', 'org', 'project')", name="ck_iam_role_scope"),
    )

    # --- iam_permission ---
    op.create_table(
        "iam_permission",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("resource", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("action", "resource"),
    )

    # --- iam_role_permission ---
    op.create_table(
        "iam_role_permission",
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("permission_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["iam_role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["iam_permission.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    # --- iam_role_binding ---
    op.create_table(
        "iam_role_binding",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("org_id", sa.String(length=36), nullable=True),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["iam_role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["organization.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "role_id", "org_id"),
    )
    op.create_index("ix_iam_role_binding_user_id", "iam_role_binding", ["user_id"])
    op.create_index("ix_iam_role_binding_role_id", "iam_role_binding", ["role_id"])
    op.create_index("ix_iam_role_binding_org_id", "iam_role_binding", ["org_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("iam_role_binding")
    op.drop_table("iam_role_permission")
    op.drop_table("iam_permission")
    op.drop_table("iam_role")
    op.drop_table("refresh_token")
    op.drop_table("login_audit")
    op.drop_table("membership")
    op.drop_table("user_account")
    op.drop_table("organization")
