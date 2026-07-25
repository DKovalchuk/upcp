"""Dashboard API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.reporting.dashboard import DashboardService
from app.reporting.schemas import (
    AuditEventSummary,
    DashboardStatsResponse,
    ProjectSummary,
    TaskCountsByStatus,
)
from app.shared.database import get_session

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(session: Session = Depends(get_session)) -> DashboardStatsResponse:  # noqa: B008
    """Get aggregated dashboard statistics."""
    service = DashboardService(session)
    stats = service.get_stats()
    return DashboardStatsResponse(
        project_count=stats["project_count"],
        task_counts_by_status=TaskCountsByStatus(**stats["task_counts_by_status"]),
        recent_projects=[ProjectSummary(**p) for p in stats["recent_projects"]],
        recent_activity=[AuditEventSummary(**a) for a in stats["recent_activity"]],
    )
