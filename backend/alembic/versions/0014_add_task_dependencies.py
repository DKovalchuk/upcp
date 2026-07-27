"""add task_dependency

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | Sequence[str] | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "task_dependency",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("task.id"), nullable=False),
        sa.Column("blocked_by_task_id", sa.String(36), sa.ForeignKey("task.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("task_id", "blocked_by_task_id", name="uq_task_dependency_pair"),
        sa.CheckConstraint("task_id != blocked_by_task_id", name="ck_no_self_dependency"),
    )
    op.create_index(
        "ix_task_dependency_task_id",
        "task_dependency",
        ["task_id"],
    )
    op.create_index(
        "ix_task_dependency_blocked_by",
        "task_dependency",
        ["blocked_by_task_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_task_dependency_blocked_by", table_name="task_dependency")
    op.drop_index("ix_task_dependency_task_id", table_name="task_dependency")
    op.drop_table("task_dependency")
