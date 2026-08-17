"""0023 — Add evidence file upload fields.

Revision ID: 0023
Revises: 0022
Create Date: 2026-08-17
"""

import sqlalchemy as sa
from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("evidence", sa.Column("file_path", sa.String(1024), nullable=True))
    op.add_column("evidence", sa.Column("file_name", sa.String(255), nullable=True))
    op.add_column("evidence", sa.Column("file_size", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("evidence", "file_size")
    op.drop_column("evidence", "file_name")
    op.drop_column("evidence", "file_path")
