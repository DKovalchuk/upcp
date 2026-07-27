"""add notification table

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | Sequence[str] | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notification_user_id", "notification", ["user_id"])
    op.create_index("ix_notification_is_read", "notification", ["is_read"])


def downgrade() -> None:
    op.drop_index("ix_notification_is_read", table_name="notification")
    op.drop_index("ix_notification_user_id", table_name="notification")
    op.drop_table("notification")
