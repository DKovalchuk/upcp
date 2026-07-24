from sqlalchemy import func
from sqlalchemy.orm import Session

from app.delivery.models import Task
from app.projects.models import Project
from app.reporting.models import Report


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
        feature_ids = [f.id for f in self._session.query(Feature.id).filter(Feature.project_id == project_id).all()]
        
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
            self._session.query(Task)
            .filter(Task.feature_id.in_(feature_ids))
            .order_by(Task.updated_at.desc())
            .limit(10)
            .all()
        ) if feature_ids else []

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