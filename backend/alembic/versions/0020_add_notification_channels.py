"""0020 — Add notification channels and delivery tracking.

Revision ID: 0020
Revises: 0019
Create Date: 2026-08-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_channel",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("channel_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("config", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_notification_channel_type", "notification_channel", ["channel_type"])
    op.create_index("ix_notification_channel_active", "notification_channel", ["is_active"])

    op.create_table(
        "notification_delivery",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "notification_id",
            sa.String(36),
            sa.ForeignKey("notification.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "channel_id",
            sa.String(36),
            sa.ForeignKey("notification_channel.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_notification_delivery_notification", "notification_delivery", ["notification_id"]
    )
    op.create_index("ix_notification_delivery_channel", "notification_delivery", ["channel_id"])
    op.create_index("ix_notification_delivery_status", "notification_delivery", ["status"])


def downgrade() -> None:
    op.drop_table("notification_delivery")
    op.drop_table("notification_channel")
