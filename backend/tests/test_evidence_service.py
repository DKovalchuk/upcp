"""Tests for Evidence service and API endpoints — TASK-0078."""

import pytest
from app.delivery.models import Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.quality.service import EvidenceService
from app.shared.database import Base
from app.shared.errors import Conflict, NotFound

from tests.conftest import _test_engine, _TestSession


@pytest.fixture()
def _db():
    import app.audit.models  # noqa: F401
    import app.delivery.models  # noqa: F401
    import app.gitread.models  # noqa: F401
    import app.identity.agents  # noqa: F401
    import app.identity.models  # noqa: F401
    import app.identity.rbac  # noqa: F401
    import app.projects.models  # noqa: F401
    import app.quality.models  # noqa: F401
    import app.reporting.models  # noqa: F401
    import app.structure.models  # noqa: F401

    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def session(_db):
    s = _TestSession()
    yield s
    s.close()


@pytest.fixture()
def project(session):
    p = Project(name="Test", slug="test")
    session.add(p)
    session.flush()
    return p


@pytest.fixture()
def feature(session, project):
    f = Feature(project_id=project.id, name="F1", slug="f1")
    session.add(f)
    session.flush()
    return f


@pytest.fixture()
def task(session, feature):
    t = Task(feature_id=feature.id, title="T1", status="in_progress")
    session.add(t)
    session.flush()
    return t


class TestEvidenceService:
    def test_create(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="commit",
            title="Initial commit",
            created_by_type="agent",
            created_by_id="a1",
        )
        assert e.id is not None
        assert e.verification_state == "unverified"
        assert e.type == "commit"

    def test_create_with_all_fields(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="test_output",
            title="pytest output",
            description="All tests pass",
            url="https://ci.example.com/123",
            content_snippet="12 passed",
            artifact_ref="build/123",
            dod_item_id=None,
            created_by_type="agent",
            created_by_id="a1",
        )
        assert e.description == "All tests pass"
        assert e.url == "https://ci.example.com/123"

    def test_get(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="screenshot",
            title="UI screenshot",
            created_by_type="human",
            created_by_id="u1",
        )
        found = svc.get(e.id)
        assert found.id == e.id

    def test_get_not_found(self, session):
        svc = EvidenceService(session)
        with pytest.raises(NotFound):
            svc.get("nonexistent")

    def test_list_by_task(self, session, task):
        svc = EvidenceService(session)
        svc.create(
            task_id=task.id,
            type="commit",
            title="C1",
            created_by_type="agent",
            created_by_id="a1",
        )
        svc.create(
            task_id=task.id,
            type="test_output",
            title="T1",
            created_by_type="agent",
            created_by_id="a1",
        )
        items = svc.list_by_task(task.id)
        assert len(items) == 2

    def test_verify_agent(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="commit",
            title="C1",
            created_by_type="agent",
            created_by_id="a1",
        )
        verified = svc.verify(e.id, verified_by_type="agent", verified_by_id="a1")
        assert verified.verification_state == "agent_verified"
        assert verified.verified_at is not None

    def test_accept_human(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="commit",
            title="C1",
            created_by_type="agent",
            created_by_id="a1",
        )
        accepted = svc.accept(e.id, verified_by_type="human", verified_by_id="u1")
        assert accepted.verification_state == "human_accepted"

    def test_reject(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="screenshot",
            title="S1",
            created_by_type="agent",
            created_by_id="a1",
        )
        rejected = svc.reject(e.id, verified_by_type="human", verified_by_id="u1")
        assert rejected.verification_state == "rejected"

    def test_verify_already_accepted_rejects(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="commit",
            title="C1",
            created_by_type="agent",
            created_by_id="a1",
        )
        svc.accept(e.id, verified_by_type="human", verified_by_id="u1")
        with pytest.raises(Conflict):
            svc.verify(e.id, verified_by_type="agent", verified_by_id="a1")

    def test_reject_already_accepted_rejects(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="commit",
            title="C1",
            created_by_type="agent",
            created_by_id="a1",
        )
        svc.accept(e.id, verified_by_type="human", verified_by_id="u1")
        with pytest.raises(Conflict):
            svc.reject(e.id, verified_by_type="human", verified_by_id="u2")

    def test_verify_already_rejected_rejects(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="commit",
            title="C1",
            created_by_type="agent",
            created_by_id="a1",
        )
        svc.reject(e.id, verified_by_type="human", verified_by_id="u1")
        with pytest.raises(Conflict):
            svc.verify(e.id, verified_by_type="agent", verified_by_id="a1")
