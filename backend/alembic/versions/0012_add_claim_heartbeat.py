"""add task_claim and heartbeat

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | Sequence[str] | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "task_claim",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("task.id"), nullable=False),
        sa.Column("agent_id", sa.String(255), nullable=False),
        sa.Column("state", sa.String(50), nullable=False, server_default="active"),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("context_snapshot", sa.Text, nullable=True),
    )
    # Partial unique index: only one active claim per task
    op.create_index(
        "uq_task_claim_active",
        "task_claim",
        ["task_id"],
        unique=True,
        postgresql_where=sa.text("state = 'active'"),
        sqlite_where=sa.text("state = 'active'"),
    )

    op.create_table(
        "heartbeat",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("claim_id", sa.String(36), sa.ForeignKey("task_claim.id"), nullable=False),
        sa.Column("progress_percent", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("current_step", sa.String(255), nullable=False),
        sa.Column("next_step", sa.String(255), nullable=False),
        sa.Column("blockers", sa.Text, nullable=True),
        sa.Column("eta", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("heartbeat")
    op.drop_index("uq_task_claim_active", table_name="task_claim")
    op.drop_table("task_claim")
