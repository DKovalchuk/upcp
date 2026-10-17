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
    # 0021 already added file_path/file_name/file_size (512) — 0023 ran after
    # it in the linear chain, so unconditional add_column always raised
    # DuplicateColumn. Add what is missing; widen file_path to 1024.
    inspector = sa.inspect(op.get_bind())
    existing = {c["name"] for c in inspector.get_columns("evidence")}
    if "file_path" not in existing:
        op.add_column("evidence", sa.Column("file_path", sa.String(1024), nullable=True))
    else:
        op.alter_column(
            "evidence", "file_path", type_=sa.String(1024), existing_type=sa.String(512)
        )
    if "file_name" not in existing:
        op.add_column("evidence", sa.Column("file_name", sa.String(255), nullable=True))
    if "file_size" not in existing:
        op.add_column("evidence", sa.Column("file_size", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("evidence", "file_size")
    op.drop_column("evidence", "file_name")
    op.drop_column("evidence", "file_path")
