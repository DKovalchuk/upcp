"""add clarification_request

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | Sequence[str] | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clarification_request",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("task.id"), nullable=False),
        sa.Column("author_type", sa.String(50), nullable=False),
        sa.Column("author_id", sa.String(36), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("context", sa.Text, nullable=True),
        sa.Column("blocking", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("state", sa.String(50), nullable=False, server_default="open"),
        sa.Column("answer", sa.Text, nullable=True),
        sa.Column("answered_by", sa.String(36), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_clarification_request_task_id",
        "clarification_request",
        ["task_id"],
    )
    op.create_index(
        "ix_clarification_request_state",
        "clarification_request",
        ["state"],
    )


def downgrade() -> None:
    op.drop_index("ix_clarification_request_state", table_name="clarification_request")
    op.drop_index("ix_clarification_request_task_id", table_name="clarification_request")
    op.drop_table("clarification_request")
