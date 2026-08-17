"""add agent_inbox_event table

Revision ID: 0018
Revises: 0017
Create Date: 2026-08-11

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | Sequence[str] | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_inbox_event",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("agent_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_inbox_event_agent_id", "agent_inbox_event", ["agent_id"])
    op.create_index("ix_agent_inbox_event_created_at", "agent_inbox_event", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_agent_inbox_event_created_at", table_name="agent_inbox_event")
    op.drop_index("ix_agent_inbox_event_agent_id", table_name="agent_inbox_event")
    op.drop_table("agent_inbox_event")
