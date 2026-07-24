"""add report

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("content", sa.JSON, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_report_project_id", "report", ["project_id"])
    op.create_index("ix_report_report_type", "report", ["report_type"])
    op.create_index("ix_report_created_at", "report", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_report_created_at")
    op.drop_index("ix_report_report_type")
    op.drop_index("ix_report_project_id")
    op.drop_table("report")