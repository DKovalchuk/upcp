"""add rbac

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rbac_user",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "rbac_role",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
    )
    op.create_table(
        "rbac_permission",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
    )
    op.create_table(
        "user_role",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("rbac_user.id"), primary_key=True),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("rbac_role.id"), primary_key=True),
    )
    op.create_table(
        "role_permission",
        sa.Column("role_id", sa.String(36), sa.ForeignKey("rbac_role.id"), primary_key=True),
        sa.Column("permission_id", sa.String(36), sa.ForeignKey("rbac_permission.id"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("role_permission")
    op.drop_table("user_role")
    op.drop_table("rbac_permission")
    op.drop_table("rbac_role")
    op.drop_table("rbac_user")
