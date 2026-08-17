"""0022 — Add task comments.

Revision ID: 0022
Revises: 0021
Create Date: 2026-08-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comment",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("task.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author_type", sa.String(50), nullable=False),
        sa.Column("author_id", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "parent_id",
            sa.String(36),
            sa.ForeignKey("comment.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_comment_task_id", "comment", ["task_id"])
    op.create_index("ix_comment_parent_id", "comment", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_comment_parent_id", table_name="comment")
    op.drop_index("ix_comment_task_id", table_name="comment")
    op.drop_table("comment")
