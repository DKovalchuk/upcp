"""0021 — Add evidence file upload fields.

Revision ID: 0021
Revises: 0020
Create Date: 2026-08-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("evidence", sa.Column("file_path", sa.String(512), nullable=True))
    op.add_column("evidence", sa.Column("file_name", sa.String(255), nullable=True))
    op.add_column("evidence", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("evidence", sa.Column("content_type", sa.String(127), nullable=True))


def downgrade() -> None:
    op.drop_column("evidence", "content_type")
    op.drop_column("evidence", "file_size")
    op.drop_column("evidence", "file_name")
    op.drop_column("evidence", "file_path")
