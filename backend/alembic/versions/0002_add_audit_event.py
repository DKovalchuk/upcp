"""add audit_event

Revision ID: 0002
Revises: d1525917f97f
Create Date: 2026-07-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "d1525917f97f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("entity_type", sa.String(255), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("actor_type", sa.String(50), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON, nullable=True),
        sa.Column("note", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("audit_event")
