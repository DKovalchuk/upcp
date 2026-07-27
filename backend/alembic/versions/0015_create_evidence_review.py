"""add evidence, review_round, review_finding, dod_item.required_evidence_type

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | Sequence[str] | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add required_evidence_type to dod_item
    op.add_column(
        "dod_item",
        sa.Column("required_evidence_type", sa.String(50), nullable=True),
    )

    # Evidence table
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("task.id"), nullable=False),
        sa.Column("dod_item_id", sa.String(36), sa.ForeignKey("dod_item.id"), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("content_snippet", sa.Text, nullable=True),
        sa.Column("artifact_ref", sa.String(512), nullable=True),
        sa.Column("created_by_type", sa.String(50), nullable=False),
        sa.Column("created_by_id", sa.String(255), nullable=False),
        sa.Column(
            "verification_state",
            sa.String(50),
            nullable=False,
            server_default="unverified",
        ),
        sa.Column("verified_by_type", sa.String(50), nullable=True),
        sa.Column("verified_by_id", sa.String(255), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidence_task_id", "evidence", ["task_id"])
    op.create_index("ix_evidence_verification_state", "evidence", ["verification_state"])

    # ReviewRound table
    op.create_table(
        "review_round",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("task.id"), nullable=False),
        sa.Column("requested_by_type", sa.String(50), nullable=False),
        sa.Column("requested_by_id", sa.String(255), nullable=False),
        sa.Column("reviewer_type", sa.String(50), nullable=True),
        sa.Column("reviewer_id", sa.String(255), nullable=True),
        sa.Column("state", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("verdict", sa.String(50), nullable=True),
        sa.Column("confidence", sa.Integer, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_review_round_task_id", "review_round", ["task_id"])
    op.create_index("ix_review_round_state", "review_round", ["state"])

    # ReviewFinding table
    op.create_table(
        "review_finding",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "review_round_id",
            sa.String(36),
            sa.ForeignKey("review_round.id"),
            nullable=False,
        ),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("evidence_id", sa.String(36), sa.ForeignKey("evidence.id"), nullable=True),
        sa.Column("dod_item_id", sa.String(36), sa.ForeignKey("dod_item.id"), nullable=True),
        sa.Column("suggestion", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("review_finding")
    op.drop_index("ix_review_round_state", table_name="review_round")
    op.drop_index("ix_review_round_task_id", table_name="review_round")
    op.drop_table("review_round")
    op.drop_index("ix_evidence_verification_state", table_name="evidence")
    op.drop_index("ix_evidence_task_id", table_name="evidence")
    op.drop_table("evidence")
    op.drop_column("dod_item", "required_evidence_type")
