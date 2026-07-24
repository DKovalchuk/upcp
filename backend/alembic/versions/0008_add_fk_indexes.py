"""add fk indexes

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-24

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_component_project_id", "component", ["project_id"])
    op.create_index("ix_module_component_id", "module", ["component_id"])
    op.create_index("ix_feature_project_id", "feature", ["project_id"])
    op.create_index("ix_feature_component_id", "feature", ["component_id"])
    op.create_index("ix_task_feature_id", "task", ["feature_id"])
    op.create_index("ix_task_component_id", "task", ["component_id"])
    op.create_index("ix_task_module_id", "task", ["module_id"])
    op.create_index("ix_subtask_task_id", "subtask", ["task_id"])
    op.create_index("ix_acceptance_criterion_task_id", "acceptance_criterion", ["task_id"])
    op.create_index("ix_dod_item_task_id", "dod_item", ["task_id"])
    op.create_index("ix_audit_event_entity_type_entity_id", "audit_event", ["entity_type", "entity_id"])
    op.create_index("ix_audit_event_timestamp", "audit_event", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_audit_event_timestamp")
    op.drop_index("ix_audit_event_entity_type_entity_id")
    op.drop_index("ix_dod_item_task_id")
    op.drop_index("ix_acceptance_criterion_task_id")
    op.drop_index("ix_subtask_task_id")
    op.drop_index("ix_task_module_id")
    op.drop_index("ix_task_component_id")
    op.drop_index("ix_task_feature_id")
    op.drop_index("ix_feature_component_id")
    op.drop_index("ix_feature_project_id")
    op.drop_index("ix_module_component_id")
    op.drop_index("ix_component_project_id")
