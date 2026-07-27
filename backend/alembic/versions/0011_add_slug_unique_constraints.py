"""add slug unique constraints

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-24

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0011"
down_revision: str | Sequence[str] | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint("uq_component_project_slug", "component", ["project_id", "slug"])
    op.create_unique_constraint("uq_module_component_slug", "module", ["component_id", "slug"])
    op.create_unique_constraint("uq_feature_project_slug", "feature", ["project_id", "slug"])


def downgrade() -> None:
    op.drop_constraint("uq_feature_project_slug", "feature")
    op.drop_constraint("uq_module_component_slug", "module")
    op.drop_constraint("uq_component_project_slug", "component")
