from sqlalchemy import func
from sqlalchemy.orm import Session

from app.delivery.models import Task
from app.projects.models import Project
from app.reporting.models import Notification, Report
from app.shared.errors import NotFound


class ReportingService:
    """Service for report generation and management."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_report(
        self,
        *,
        project_id: str,
        report_type: str,
        content: dict[str, object] | None = None,
    ) -> Report:
        """Create a new report."""
        report = Report(
            project_id=project_id,
            report_type=report_type,
            content=content,
        )
        self._session.add(report)
        self._session.flush()
        return report

    def get_report(self, report_id: str) -> Report | None:
        """Get a report by ID."""
        return self._session.get(Report, report_id)

    def generate_daily_report(self, project_id: str) -> Report:
        """Generate a daily report for a project."""
        from app.delivery.models import Feature

        # Verify project exists
        project = self._session.get(Project, project_id)
        if not project:
            from app.shared.errors import NotFound

            raise NotFound(f"Project {project_id} not found")

        # Get feature IDs for this project
        feature_ids = [
            f.id
            for f in self._session.query(Feature.id).filter(Feature.project_id == project_id).all()
        ]

        # Get task counts by status
        task_counts: dict[str, int] = {}
        if feature_ids:
            rows = (
                self._session.query(Task.status, func.count(Task.id))
                .filter(Task.feature_id.in_(feature_ids))
                .group_by(Task.status)
                .all()
            )
            task_counts = {row[0]: row[1] for row in rows}

        # Get recent tasks (last 10)
        recent_tasks = (
            (
                self._session.query(Task)
                .filter(Task.feature_id.in_(feature_ids))
                .order_by(Task.updated_at.desc())
                .limit(10)
                .all()
            )
            if feature_ids
            else []
        )

        # Build report content
        content: dict[str, object] = {
            "project_name": project.name,
            "task_counts": task_counts,
            "recent_changes": [
                {
                    "task_id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "updated_at": task.updated_at.isoformat(),
                }
                for task in recent_tasks
            ],
            "blockers": [],  # Placeholder for future blocker detection
        }

        return self.create_report(
            project_id=project_id,
            report_type="daily",
            content=content,
        )

    def list_reports(
        self,
        project_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Report], int]:
        """List reports with optional filtering."""
        query = self._session.query(Report)

        if project_id:
            query = query.filter(Report.project_id == project_id)

        total = query.count()
        reports = query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()

        return reports, total

    def update_report_summary(self, report_id: str, summary: str) -> Report:
        """Update report with LLM-generated summary."""
        report = self.get_report(report_id)
        if not report:
            from app.shared.errors import NotFound

            raise NotFound(f"Report {report_id} not found")

        report.summary = summary
        self._session.flush()
        return report


class NotificationService:
    """Notification CRUD and badge count."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        user_id: str,
        type: str,
        title: str,
        message: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> Notification:
        n = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self._session.add(n)
        self._session.flush()
        return n

    def list_by_user(
        self, user_id: str, *, unread_only: bool = False, limit: int = 50
    ) -> list[Notification]:
        q = self._session.query(Notification).filter_by(user_id=user_id)
        if unread_only:
            q = q.filter_by(is_read=False)
        return q.order_by(Notification.created_at.desc()).limit(limit).all()

    def mark_read(self, notification_id: str) -> Notification:
        n = self._session.get(Notification, notification_id)
        if not n:
            raise NotFound(f"notification '{notification_id}' not found")
        n.is_read = True
        self._session.flush()
        return n

    def mark_all_read(self, user_id: str) -> int:
        count = (
            self._session.query(Notification)
            .filter_by(user_id=user_id, is_read=False)
            .update({"is_read": True})
        )
        self._session.flush()
        return count

    def unread_count(self, user_id: str) -> int:
        result = (
            self._session.query(func.count(Notification.id))
            .filter_by(user_id=user_id, is_read=False)
            .scalar()
        )
        return int(result) if result is not None else 0
