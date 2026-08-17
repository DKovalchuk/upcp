"""add missing indexes and ondelete clauses

Revision ID: 0019
Revises: 0018
Create Date: 2026-08-12

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0019"
down_revision: str | Sequence[str] | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Indexes on frequently queried FK/status columns ──────────
    _ix = [
        ("ix_task_feature_id", "task", ["feature_id"]),
        ("ix_task_status", "task", ["status"]),
        ("ix_feature_project_id", "feature", ["project_id"]),
        ("ix_component_project_id", "component", ["project_id"]),
        ("ix_module_component_id", "module", ["component_id"]),
        ("ix_project_status", "project", ["status"]),
        ("ix_report_project_id", "report", ["project_id"]),
        ("ix_task_claim_agent_id", "task_claim", ["agent_id"]),
        ("ix_audit_event_entity_id", "audit_event", ["entity_id"]),
        ("ix_audit_event_event_type", "audit_event", ["event_type"]),
        ("ix_audit_event_entity_type", "audit_event", ["entity_type"]),
        ("ix_audit_event_timestamp", "audit_event", ["timestamp"]),
        ("ix_git_provider_project_id", "git_provider", ["project_id"]),
        ("ix_git_branch_provider_id", "git_branch", ["provider_id"]),
        ("ix_git_commit_provider_id", "git_commit", ["provider_id"]),
        ("ix_git_pull_request_provider_id", "git_pull_request", ["provider_id"]),
        ("ix_git_link_entity", "git_link", ["entity_type", "entity_id"]),
    ]
    for name, table, cols in _ix:
        op.create_index(name, table, cols, unique=False)

    # ── ondelete clauses — drop old FK, re-add with ON DELETE ────
    _fk = [
        # (table, column, referred_table, referred_column, ondelete)
        ("feature", "project_id", "project", "id", "CASCADE"),
        ("feature", "component_id", "component", "id", "SET NULL"),
        ("task", "feature_id", "feature", "id", "CASCADE"),
        ("task", "component_id", "component", "id", "SET NULL"),
        ("task", "module_id", "module", "id", "SET NULL"),
        ("subtask", "task_id", "task", "id", "CASCADE"),
        ("clarification_request", "task_id", "task", "id", "CASCADE"),
        ("task_dependency", "task_id", "task", "id", "CASCADE"),
        ("task_dependency", "blocked_by_task_id", "task", "id", "CASCADE"),
        ("task_claim", "task_id", "task", "id", "CASCADE"),
        ("heartbeat", "claim_id", "task_claim", "id", "CASCADE"),
        ("component", "project_id", "project", "id", "CASCADE"),
        ("module", "component_id", "component", "id", "CASCADE"),
        ("acceptance_criterion", "task_id", "task", "id", "CASCADE"),
        ("dod_item", "task_id", "task", "id", "CASCADE"),
        ("evidence", "task_id", "task", "id", "CASCADE"),
        ("evidence", "dod_item_id", "dod_item", "id", "SET NULL"),
        ("review_round", "task_id", "task", "id", "CASCADE"),
        ("review_finding", "review_round_id", "review_round", "id", "CASCADE"),
        ("review_finding", "evidence_id", "evidence", "id", "SET NULL"),
        ("review_finding", "dod_item_id", "dod_item", "id", "SET NULL"),
        ("report", "project_id", "project", "id", "CASCADE"),
        ("git_provider", "project_id", "project", "id", "CASCADE"),
        ("git_branch", "provider_id", "git_provider", "id", "CASCADE"),
        ("git_commit", "provider_id", "git_provider", "id", "CASCADE"),
        ("git_pull_request", "provider_id", "git_provider", "id", "CASCADE"),
    ]
    for table, col, ref_table, ref_col, ondelete in _fk:
        # Drop existing FK constraint (name follows SQLAlchemy convention)
        fk_name = f"fk_{table}_{col}_{ref_table}"
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {fk_name}")
        # Re-add with ON DELETE
        op.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT {fk_name} "
            f"FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col}) ON DELETE {ondelete}"
        )


def downgrade() -> None:
    # ── Remove ondelete — restore plain FKs ──────────────────────
    _fk = [
        ("feature", "project_id", "project", "id"),
        ("feature", "component_id", "component", "id"),
        ("task", "feature_id", "feature", "id"),
        ("task", "component_id", "component", "id"),
        ("task", "module_id", "module", "id"),
        ("subtask", "task_id", "task", "id"),
        ("clarification_request", "task_id", "task", "id"),
        ("task_dependency", "task_id", "task", "id"),
        ("task_dependency", "blocked_by_task_id", "task", "id"),
        ("task_claim", "task_id", "task", "id"),
        ("heartbeat", "claim_id", "task_claim", "id"),
        ("component", "project_id", "project", "id"),
        ("module", "component_id", "component", "id"),
        ("acceptance_criterion", "task_id", "task", "id"),
        ("dod_item", "task_id", "task", "id"),
        ("evidence", "task_id", "task", "id"),
        ("evidence", "dod_item_id", "dod_item", "id"),
        ("review_round", "task_id", "task", "id"),
        ("review_finding", "review_round_id", "review_round", "id"),
        ("review_finding", "evidence_id", "evidence", "id"),
        ("review_finding", "dod_item_id", "dod_item", "id"),
        ("report", "project_id", "project", "id"),
        ("git_provider", "project_id", "project", "id"),
        ("git_branch", "provider_id", "git_provider", "id"),
        ("git_commit", "provider_id", "git_provider", "id"),
        ("git_pull_request", "provider_id", "git_provider", "id"),
    ]
    for table, col, ref_table, ref_col in _fk:
        fk_name = f"fk_{table}_{col}_{ref_table}"
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {fk_name}")
        op.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT {fk_name} "
            f"FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})"
        )

    # ── Drop indexes ─────────────────────────────────────────────
    _ix = [
        ("ix_task_feature_id", "task"),
        ("ix_task_status", "task"),
        ("ix_feature_project_id", "feature"),
        ("ix_component_project_id", "component"),
        ("ix_module_component_id", "module"),
        ("ix_project_status", "project"),
        ("ix_report_project_id", "report"),
        ("ix_task_claim_agent_id", "task_claim"),
        ("ix_audit_event_entity_id", "audit_event"),
        ("ix_audit_event_event_type", "audit_event"),
        ("ix_audit_event_entity_type", "audit_event"),
        ("ix_audit_event_timestamp", "audit_event"),
        ("ix_git_provider_project_id", "git_provider"),
        ("ix_git_branch_provider_id", "git_branch"),
        ("ix_git_commit_provider_id", "git_commit"),
        ("ix_git_pull_request_provider_id", "git_pull_request"),
        ("ix_git_link_entity", "git_link"),
    ]
    for name, table in _ix:
        op.drop_index(name, table_name=table)
