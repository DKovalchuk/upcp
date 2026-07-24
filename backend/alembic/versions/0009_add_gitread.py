"""add gitread

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | Sequence[str] | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "git_provider",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("provider_type", sa.String(50), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "git_branch",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("git_provider.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("last_commit_sha", sa.String(40), nullable=True),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "git_commit",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("git_provider.id"), nullable=False),
        sa.Column("sha", sa.String(40), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "git_pull_request",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("git_provider.id"), nullable=False),
        sa.Column("number", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("state", sa.String(50), nullable=False),
        sa.Column("head_sha", sa.String(40), nullable=True),
        sa.Column("base_branch", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "git_link",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("git_type", sa.String(50), nullable=False),
        sa.Column("git_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_git_provider_project_id", "git_provider", ["project_id"])
    op.create_index("ix_git_branch_provider_id", "git_branch", ["provider_id"])
    op.create_index("ix_git_commit_provider_id", "git_commit", ["provider_id"])
    op.create_index("ix_git_pull_request_provider_id", "git_pull_request", ["provider_id"])
    op.create_index("ix_git_link_entity", "git_link", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_git_link_entity")
    op.drop_index("ix_git_pull_request_provider_id")
    op.drop_index("ix_git_commit_provider_id")
    op.drop_index("ix_git_branch_provider_id")
    op.drop_index("ix_git_provider_project_id")
    op.drop_table("git_link")
    op.drop_table("git_pull_request")
    op.drop_table("git_commit")
    op.drop_table("git_branch")
    op.drop_table("git_provider")
