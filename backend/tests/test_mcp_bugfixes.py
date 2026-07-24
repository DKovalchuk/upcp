"""Regression tests for MCP module bugfixes — TASK-0038.

BUG-1: call_tool session bypass
BUG-2: task_list semantic mismatch (project_id vs feature_id)
BUG-3: _serialize_task crash with priority=None
BUG-4: ContextPackGenerator session bypass
BUG-5: _get_int_arg bool/empty-string handling
BUG-6: No input validation (max limit, min offset)
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from app.delivery.models import Feature, Task  # noqa: F401 — register models
from app.mcp.context_pack import ContextPackGenerator
from app.mcp.tools import (
    _get_int_arg,
    _serialize_task,
    call_tool,
)
from app.projects.models import Project  # noqa: F401 — register models
from app.shared.database import Base

from tests.conftest import _test_engine, _TestSession


@pytest.fixture()
def _db():
    """Create tables, yield, then drop."""
    # Ensure all models are imported so Base.metadata knows about them
    import app.audit.models  # noqa: F401
    import app.auth.models  # noqa: F401
    import app.delivery.models  # noqa: F401
    import app.gitread.models  # noqa: F401
    import app.projects.models  # noqa: F401
    import app.quality.models  # noqa: F401
    import app.reporting.models  # noqa: F401
    import app.structure.models  # noqa: F401

    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


# ---------------------------------------------------------------------------
# BUG-5: _get_int_arg bool/empty-string handling
# ---------------------------------------------------------------------------
class TestGetIntArgBug5:
    """_get_int_arg must handle bool, empty string, and non-string types."""

    def test_bool_true_returns_1(self) -> None:
        result = _get_int_arg({"flag": True}, "flag", 0)
        assert result == 1

    def test_bool_false_returns_0(self) -> None:
        """BUG-5: int(str(False)) == 1, but False should map to 0."""
        result = _get_int_arg({"flag": False}, "flag", 0)
        assert result == 0

    def test_int_value_passthrough(self) -> None:
        result = _get_int_arg({"offset": 42}, "offset", 0)
        assert result == 42

    def test_float_value_converted(self) -> None:
        result = _get_int_arg({"offset": 3.0}, "offset", 0)
        assert result == 3

    def test_string_numeric(self) -> None:
        result = _get_int_arg({"offset": "10"}, "offset", 0)
        assert result == 10

    def test_empty_string_raises(self) -> None:
        """BUG-5: empty string should raise ValueError, not silently use default."""
        with pytest.raises(ValueError, match="not a valid integer"):
            _get_int_arg({"offset": ""}, "offset", 0)

    def test_non_numeric_string_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid integer"):
            _get_int_arg({"offset": "abc"}, "offset", 0)

    def test_none_returns_default(self) -> None:
        result = _get_int_arg({"other": 1}, "offset", 0)
        assert result == 0

    def test_missing_key_returns_default(self) -> None:
        result = _get_int_arg({}, "offset", 99)
        assert result == 99


# ---------------------------------------------------------------------------
# BUG-6: Input validation (max limit, min offset)
# ---------------------------------------------------------------------------
class TestInputValidationBug6:
    """All handlers must enforce limit <= 100, offset >= 0."""

    def test_project_list_limit_capped(self, _db) -> None:
        """limit=500 must be capped to 100."""
        session = _TestSession()
        try:
            from app.mcp.tools import _handle_project_list

            result = _handle_project_list(session, {"offset": 0, "limit": 500})
            parsed = json.loads(result.content[0]["text"])
            assert parsed["limit"] <= 100
        finally:
            session.close()

    def test_project_list_offset_negative(self, _db) -> None:
        """offset=-5 must be clamped to 0."""
        session = _TestSession()
        try:
            from app.mcp.tools import _handle_project_list

            result = _handle_project_list(session, {"offset": -5, "limit": 10})
            parsed = json.loads(result.content[0]["text"])
            assert parsed["offset"] >= 0
        finally:
            session.close()

    def test_feature_list_limit_capped(self, _db) -> None:
        session = _TestSession()
        try:
            from app.mcp.tools import _handle_feature_list

            # Need a valid project_id for feature_list, but we test limit capping
            # even with empty result
            result = _handle_feature_list(
                session, {"project_id": "nonexistent", "offset": 0, "limit": 999}
            )
            parsed = json.loads(result.content[0]["text"])
            assert parsed["limit"] <= 100
        finally:
            session.close()

    def test_task_list_limit_capped(self, _db) -> None:
        session = _TestSession()
        try:
            from app.mcp.tools import _handle_task_list

            result = _handle_task_list(
                session, {"project_id": "nonexistent", "offset": 0, "limit": 500}
            )
            parsed = json.loads(result.content[0]["text"])
            assert parsed["limit"] <= 100
        finally:
            session.close()


# ---------------------------------------------------------------------------
# BUG-3: _serialize_task crash with priority=None
# ---------------------------------------------------------------------------
class TestSerializeTaskBug3:
    """_serialize_task must handle priority=None gracefully."""

    def test_task_with_priority_none(self) -> None:
        task = MagicMock()
        task.id = "t1"
        task.feature_id = "f1"
        task.title = "Test"
        task.description = None
        task.status = "backlog"
        task.priority = None  # BUG-3 trigger
        task.assignee_type = None
        task.assignee_id = None
        task.component_id = None
        task.module_id = None
        task.created_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")
        task.updated_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")

        result = _serialize_task(task)
        assert result["priority"] is None

    def test_task_with_priority_int(self) -> None:
        task = MagicMock()
        task.id = "t1"
        task.feature_id = "f1"
        task.title = "Test"
        task.description = None
        task.status = "backlog"
        task.priority = 5
        task.assignee_type = None
        task.assignee_id = None
        task.component_id = None
        task.module_id = None
        task.created_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")
        task.updated_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")

        result = _serialize_task(task)
        assert result["priority"] == 5


# ---------------------------------------------------------------------------
# BUG-1: call_tool session bypass
# ---------------------------------------------------------------------------
class TestCallToolSessionBug1:
    """call_tool must use the provided session, not create SessionLocal()."""

    @pytest.mark.asyncio
    async def test_call_tool_uses_provided_session(self) -> None:
        """BUG-1: call_tool should accept session param and NOT call SessionLocal."""
        mock_session = MagicMock()
        with patch("app.mcp.tools.SessionLocal") as mock_session_local:
            await call_tool("project_list", {"offset": 0, "limit": 10}, session=mock_session)
            # SessionLocal should NOT have been called
            mock_session_local.assert_not_called()

    @pytest.mark.asyncio
    async def test_call_tool_without_session_uses_sessionlocal(self) -> None:
        """Backward compat: no session param should create SessionLocal."""
        mock_session = MagicMock()
        with patch("app.mcp.tools.SessionLocal", return_value=mock_session):
            mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = ([], 0)
            mock_session.query.return_value.count.return_value = 0
            await call_tool("project_list", {"offset": 0, "limit": 10})
            # SessionLocal SHOULD have been called
            mock_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# BUG-2: task_list semantic mismatch
# ---------------------------------------------------------------------------
class TestTaskListByProjectBug2:
    """task_list tool must accept project_id and list tasks via features."""

    def test_task_list_returns_tasks_for_project(self, _db) -> None:
        """BUG-2: task_list(project_id=...) should find tasks through features."""
        session = _TestSession()
        try:
            project = Project(name="P1", slug="p1")
            session.add(project)
            session.flush()

            feature = Feature(project_id=project.id, name="F1", slug="f1")
            session.add(feature)
            session.flush()

            task = Task(feature_id=feature.id, title="T1", priority=1)
            session.add(task)
            session.commit()

            from app.mcp.tools import _handle_task_list

            result = _handle_task_list(session, {"project_id": project.id})
            parsed = json.loads(result.content[0]["text"])
            assert parsed["total"] == 1
            assert parsed["items"][0]["title"] == "T1"
        finally:
            session.close()

    def test_task_list_empty_project(self, _db) -> None:
        session = _TestSession()
        try:
            project = Project(name="P2", slug="p2")
            session.add(project)
            session.commit()

            from app.mcp.tools import _handle_task_list

            result = _handle_task_list(session, {"project_id": project.id})
            parsed = json.loads(result.content[0]["text"])
            assert parsed["total"] == 0
            assert parsed["items"] == []
        finally:
            session.close()


# ---------------------------------------------------------------------------
# BUG-4: ContextPackGenerator session bypass
# ---------------------------------------------------------------------------
class TestContextPackSessionBug4:
    """ContextPackGenerator must accept session, not create SessionLocal."""

    def test_context_pack_accepts_session(self, _db) -> None:
        """BUG-4: ContextPackGenerator should work with injected session."""
        session = _TestSession()
        try:
            project = Project(name="P3", slug="p3", description="Test project")
            session.add(project)
            session.commit()

            generator = ContextPackGenerator()
            result = generator.generate_project_context(project.id, session=session)
            assert "P3" in result
            assert "Test project" in result
        finally:
            session.close()

    def test_context_pack_without_session_uses_sessionlocal(self) -> None:
        """Backward compat: no session param should create SessionLocal."""
        mock_session = MagicMock()
        project_mock = MagicMock()
        project_mock.name = "P4"
        project_mock.slug = "p4"
        project_mock.status = "active"
        project_mock.description = None

        with patch("app.mcp.context_pack.SessionLocal", return_value=mock_session):
            # ProjectService.get calls session.get(Model, id)
            mock_session.get.return_value = project_mock
            # list_tasks_by_project returns empty
            mock_session.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
            mock_session.query.return_value.join.return_value.filter.return_value.count.return_value = 0
            # GitLinkService.list_by_entity returns empty
            mock_session.query.return_value.filter_by.return_value.all.return_value = []

            generator = ContextPackGenerator()
            result = generator.generate_project_context("pid")
            assert "P4" in result
            mock_session.close.assert_called_once()
