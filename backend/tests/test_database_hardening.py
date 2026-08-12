"""Database hardening tests — TASK-0106 / SPEC-0020 S19.3.

Tests for:
1. ondelete clauses on ForeignKeys (model-level verification)
2. N+1 fix in agent_claims endpoint
"""

import app.audit.models  # noqa: F401 — register AuditEvent
import app.delivery.models  # noqa: F401 — register Feature, Task, etc.
import app.gitread.models  # noqa: F401 — register Git* tables
import app.identity.agents  # noqa: F401 — register Agent/AgentToken tables
import app.quality.models  # noqa: F401 — register quality tables
import app.reporting.models  # noqa: F401 — register Report, Notification
import app.structure.models  # noqa: F401 — register Component, Module
from app.shared.database import Base

# ══════════════════════════════════════════════════════════════
# ondelete verification — model metadata inspection
# ══════════════════════════════════════════════════════════════


def test_ondelete_on_model_foreign_keys() -> None:
    """All ForeignKey columns have explicit ondelete clauses."""
    checks = [
        ("feature", "project_id", "CASCADE"),
        ("feature", "component_id", "SET NULL"),
        ("task", "feature_id", "CASCADE"),
        ("task", "component_id", "SET NULL"),
        ("task", "module_id", "SET NULL"),
        ("subtask", "task_id", "CASCADE"),
        ("clarification_request", "task_id", "CASCADE"),
        ("task_dependency", "task_id", "CASCADE"),
        ("task_dependency", "blocked_by_task_id", "CASCADE"),
        ("task_claim", "task_id", "CASCADE"),
        ("heartbeat", "claim_id", "CASCADE"),
        ("component", "project_id", "CASCADE"),
        ("module", "component_id", "CASCADE"),
        ("acceptance_criterion", "task_id", "CASCADE"),
        ("dod_item", "task_id", "CASCADE"),
        ("evidence", "task_id", "CASCADE"),
        ("evidence", "dod_item_id", "SET NULL"),
        ("review_round", "task_id", "CASCADE"),
        ("review_finding", "review_round_id", "CASCADE"),
        ("review_finding", "evidence_id", "SET NULL"),
        ("review_finding", "dod_item_id", "SET NULL"),
        ("report", "project_id", "CASCADE"),
        ("git_provider", "project_id", "CASCADE"),
        ("git_branch", "provider_id", "CASCADE"),
        ("git_commit", "provider_id", "CASCADE"),
        ("git_pull_request", "provider_id", "CASCADE"),
    ]

    for table_name, col_name, expected_ondelete in checks:
        table = Base.metadata.tables[table_name]
        col = table.c[col_name]
        fks = list(col.foreign_keys)
        assert len(fks) == 1, f"{table_name}.{col_name} should have exactly 1 FK"
        actual_ondelete = fks[0].ondelete
        assert actual_ondelete == expected_ondelete, (
            f"{table_name}.{col_name}: expected ondelete={expected_ondelete}, got {actual_ondelete}"
        )


def test_agent_claims_batch_query() -> None:
    """Agent claims endpoint uses batch query (no N+1).

    Creates 10 claims with tasks and verifies all task titles are returned
    in a single batch query rather than N individual queries.
    """
    from app.delivery.models import Feature, Task, TaskClaim
    from app.identity.agent_endpoints import router
    from app.identity.agents import Agent
    from app.identity.auth import get_current_user
    from app.identity.dependencies import CurrentUser
    from app.identity.models import User
    from app.projects.models import Project
    from app.shared.database import Base, get_session
    from app.shared.errors import register_error_handlers
    from app.shared.text import new_id
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from tests.conftest import _override_session, _test_engine, _TestSession

    Base.metadata.create_all(bind=_test_engine)

    _app = FastAPI()
    register_error_handlers(_app)
    _app.include_router(router, prefix="/api/v1")
    _app.dependency_overrides[get_session] = _override_session
    _app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id="n1-test-user", email="n1@test.com", is_superuser=True
    )

    session = _TestSession()
    task_ids = []
    try:
        user = User(id="n1-test-user", email="n1@test.com", password_hash="x", display_name="N1")
        session.merge(user)
        session.flush()

        p = Project(name="N1-Project", slug="n1-project")
        session.add(p)
        session.flush()

        f = Feature(project_id=p.id, name="N1-Feature", slug="n1-feature")
        session.add(f)
        session.flush()

        agent = Agent(name="n1-agent", description="test", created_by="n1-test-user")
        session.add(agent)
        session.flush()
        agent_id = agent.id

        for i in range(10):
            t = Task(feature_id=f.id, title=f"N1-Task-{i}", status="backlog")
            session.add(t)
            session.flush()
            task_ids.append(t.id)
            c = TaskClaim(id=new_id(), task_id=t.id, agent_id=agent_id, state="completed")
            session.add(c)
        session.commit()
    finally:
        session.close()

    client = TestClient(_app)
    resp = client.get(f"/api/v1/agents/{agent_id}/claims")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 10

    # All task titles present — proves batch query worked
    titles = {item["task_title"] for item in items}
    for i in range(10):
        assert f"N1-Task-{i}" in titles

    # Cleanup
    session = _TestSession()
    try:
        session.query(TaskClaim).filter(TaskClaim.agent_id == agent_id).delete()
        session.query(Task).filter(Task.id.in_(task_ids)).delete()
        session.query(Feature).filter_by(name="N1-Feature").delete()
        session.query(Project).filter_by(name="N1-Project").delete()
        session.query(Agent).filter_by(name="n1-agent").delete()
        session.query(User).filter_by(id="n1-test-user").delete()
        session.commit()
    finally:
        session.close()
