"""Unit tests for reporting services."""

import uuid

import pytest
from app.delivery.models import Feature, Task
from app.projects.models import Project
from app.reporting.service import NotificationService, ReportingService
from app.shared.errors import NotFound
from sqlalchemy.orm import Session


@pytest.fixture()
def project(db_session: Session) -> Project:
    """Create a test project."""
    slug = f"rtest-{uuid.uuid4().hex[:8]}"
    project = Project(name="Test Project", slug=slug)
    db_session.add(project)
    db_session.flush()
    return project


@pytest.fixture()
def feature(db_session: Session, project: Project) -> Feature:
    """Create a test feature."""
    slug = f"rfeat-{uuid.uuid4().hex[:8]}"
    feature = Feature(project_id=project.id, name="Test Feature", slug=slug)
    db_session.add(feature)
    db_session.flush()
    return feature


@pytest.fixture()
def task(db_session: Session, feature: Feature) -> Task:
    """Create a test task."""
    task = Task(feature_id=feature.id, title="Test Task", status="todo")
    db_session.add(task)
    db_session.flush()
    return task


class TestReportingService:
    """Tests for ReportingService."""

    def test_create_report(self, db_session: Session, project: Project) -> None:
        """Test basic report creation."""
        service = ReportingService(db_session)
        report = service.create_report(
            project_id=project.id,
            report_type="daily",
            content={"tasks": 5},
        )
        assert report.id is not None
        assert report.project_id == project.id
        assert report.report_type == "daily"
        assert report.content == {"tasks": 5}
        assert report.summary is None

    def test_create_report_without_content(self, db_session: Session, project: Project) -> None:
        """Test report creation with no content."""
        service = ReportingService(db_session)
        report = service.create_report(project_id=project.id, report_type="weekly")
        assert report.content is None

    def test_get_report(self, db_session: Session, project: Project) -> None:
        """Test fetching a report by ID."""
        service = ReportingService(db_session)
        created = service.create_report(project_id=project.id, report_type="daily")
        fetched = service.get_report(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_report_not_found(self, db_session: Session) -> None:
        """Test fetching a non-existent report."""
        service = ReportingService(db_session)
        result = service.get_report("non-existent-id")
        assert result is None

    def test_list_reports_empty(self, db_session: Session, project: Project) -> None:
        """Test listing reports when none exist."""
        service = ReportingService(db_session)
        reports, total = service.list_reports(project_id=project.id)
        assert reports == []
        assert total == 0

    def test_list_reports_with_data(self, db_session: Session, project: Project) -> None:
        """Test listing reports with existing data."""
        service = ReportingService(db_session)
        service.create_report(project_id=project.id, report_type="daily")
        service.create_report(project_id=project.id, report_type="weekly")

        reports, total = service.list_reports(project_id=project.id)
        assert total == 2
        assert len(reports) == 2

    def test_list_reports_pagination(self, db_session: Session, project: Project) -> None:
        """Test report list pagination."""
        service = ReportingService(db_session)
        for i in range(5):
            service.create_report(project_id=project.id, report_type=f"type-{i}")

        reports_page1, total = service.list_reports(project_id=project.id, offset=0, limit=2)
        assert len(reports_page1) == 2
        assert total == 5

        reports_page2, _ = service.list_reports(project_id=project.id, offset=2, limit=2)
        assert len(reports_page2) == 2
        assert reports_page1[0].id != reports_page2[0].id

    def test_update_report_summary(self, db_session: Session, project: Project) -> None:
        """Test updating report summary."""
        service = ReportingService(db_session)
        report = service.create_report(project_id=project.id, report_type="daily")
        updated = service.update_report_summary(report.id, "Summary text")
        assert updated.summary == "Summary text"

    def test_update_report_summary_not_found(self, db_session: Session) -> None:
        """Test updating summary for non-existent report raises NotFound."""
        service = ReportingService(db_session)
        with pytest.raises(NotFound):
            service.update_report_summary("non-existent-id", "summary")

    def test_generate_daily_report(
        self, db_session: Session, project: Project, feature: Feature, task: Task
    ) -> None:
        """Test daily report generation with task stats."""
        service = ReportingService(db_session)
        report = service.generate_daily_report(project.id)

        assert report.report_type == "daily"
        assert report.content is not None
        content = report.content
        assert content["project_name"] == project.name
        assert "task_counts" in content
        assert "recent_changes" in content

    def test_generate_daily_report_with_tasks(
        self, db_session: Session, project: Project, feature: Feature
    ) -> None:
        """Test daily report with multiple tasks."""
        service = ReportingService(db_session)
        for i in range(3):
            task = Task(
                feature_id=feature.id,
                title=f"Task {i}",
                status="todo" if i % 2 == 0 else "done",
            )
            db_session.add(task)
        db_session.flush()

        report = service.generate_daily_report(project.id)
        assert report.content is not None
        assert report.content["task_counts"]["todo"] == 2
        assert report.content["task_counts"]["done"] == 1

    def test_generate_daily_report_no_project(self, db_session: Session) -> None:
        """Test daily report generation for non-existent project."""
        service = ReportingService(db_session)
        with pytest.raises(NotFound):
            service.generate_daily_report("non-existent-project")

    def test_generate_daily_report_no_tasks(self, db_session: Session, project: Project) -> None:
        """Test daily report when project has no tasks."""
        service = ReportingService(db_session)
        report = service.generate_daily_report(project.id)
        assert report.content is not None
        assert report.content["task_counts"] == {}
        assert report.content["recent_changes"] == []


class TestNotificationService:
    """Tests for NotificationService."""

    def test_create_notification(self, db_session: Session) -> None:
        """Test basic notification creation."""
        service = NotificationService(db_session)
        notification = service.create(
            user_id="user-123",
            type="info",
            title="Test Title",
            message="Test message content",
        )
        assert notification.id is not None
        assert notification.user_id == "user-123"
        assert notification.type == "info"
        assert notification.title == "Test Title"
        assert notification.message == "Test message content"
        assert notification.is_read is False

    def test_create_notification_with_entity(self, db_session: Session) -> None:
        """Test notification creation with entity reference."""
        service = NotificationService(db_session)
        notification = service.create(
            user_id="user-123",
            type="mention",
            title="Mention",
            message="You were mentioned",
            entity_type="task",
            entity_id="task-456",
        )
        assert notification.entity_type == "task"
        assert notification.entity_id == "task-456"

    def test_list_notifications_empty(self, db_session: Session) -> None:
        """Test listing notifications when none exist."""
        service = NotificationService(db_session)
        notifications = service.list_by_user("user-123")
        assert notifications == []

    def test_list_notifications_by_user(self, db_session: Session) -> None:
        """Test listing notifications filtered by user."""
        service = NotificationService(db_session)
        service.create(user_id="user-1", type="info", title="1", message="m1")
        service.create(user_id="user-2", type="info", title="2", message="m2")
        service.create(user_id="user-1", type="info", title="3", message="m3")

        notifications = service.list_by_user("user-1")
        assert len(notifications) == 2

    def test_list_notifications_unread_only(self, db_session: Session) -> None:
        """Test listing only unread notifications."""
        service = NotificationService(db_session)
        n1 = service.create(user_id="user-1", type="info", title="1", message="m1")
        n2 = service.create(user_id="user-1", type="info", title="2", message="m2")
        service.mark_read(n1.id)

        unread = service.list_by_user("user-1", unread_only=True)
        assert len(unread) == 1
        assert unread[0].id == n2.id

    def test_list_notifications_limit(self, db_session: Session) -> None:
        """Test notification list with limit."""
        service = NotificationService(db_session)
        for i in range(10):
            service.create(user_id="user-1", type="info", title=f"{i}", message=f"m{i}")

        notifications = service.list_by_user("user-1", limit=3)
        assert len(notifications) == 3

    def test_mark_read(self, db_session: Session) -> None:
        """Test marking a notification as read."""
        service = NotificationService(db_session)
        notification = service.create(user_id="user-1", type="info", title="T", message="M")
        assert notification.is_read is False

        updated = service.mark_read(notification.id)
        assert updated.is_read is True

    def test_mark_read_not_found(self, db_session: Session) -> None:
        """Test marking non-existent notification as read."""
        service = NotificationService(db_session)
        with pytest.raises(NotFound):
            service.mark_read("non-existent-id")

    def test_mark_all_read(self, db_session: Session) -> None:
        """Test marking all notifications as read for a user."""
        service = NotificationService(db_session)
        service.create(user_id="user-1", type="info", title="1", message="m1")
        service.create(user_id="user-1", type="info", title="2", message="m2")
        service.create(user_id="user-1", type="info", title="3", message="m3")

        count = service.mark_all_read("user-1")
        assert count == 3

        unread = service.list_by_user("user-1", unread_only=True)
        assert len(unread) == 0

    def test_mark_all_read_partial(self, db_session: Session) -> None:
        """Test mark_all_read when some are already read."""
        service = NotificationService(db_session)
        n1 = service.create(user_id="user-1", type="info", title="1", message="m1")
        service.create(user_id="user-1", type="info", title="2", message="m2")
        service.mark_read(n1.id)

        count = service.mark_all_read("user-1")
        assert count == 1  # Only one was unread

    def test_unread_count(self, db_session: Session) -> None:
        """Test unread notification count."""
        service = NotificationService(db_session)
        assert service.unread_count("user-1") == 0

        service.create(user_id="user-1", type="info", title="1", message="m1")
        service.create(user_id="user-1", type="info", title="2", message="m2")
        assert service.unread_count("user-1") == 2

    def test_unread_count_after_read(self, db_session: Session) -> None:
        """Test unread count updates after marking read."""
        service = NotificationService(db_session)
        n1 = service.create(user_id="user-1", type="info", title="1", message="m1")
        service.create(user_id="user-1", type="info", title="2", message="m2")

        service.mark_read(n1.id)
        assert service.unread_count("user-1") == 1

    def test_unread_count_isolation(self, db_session: Session) -> None:
        """Test unread count is per-user."""
        service = NotificationService(db_session)
        service.create(user_id="user-1", type="info", title="1", message="m1")
        service.create(user_id="user-2", type="info", title="2", message="m2")

        assert service.unread_count("user-1") == 1
        assert service.unread_count("user-2") == 1
        assert service.unread_count("user-3") == 0
