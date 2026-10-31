"""Dashboard API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.projects.models import Project
from app.reporting.attention import AttentionDashboardService
from app.reporting.dashboard import DashboardService
from app.reporting.portfolio import PortfolioService
from app.reporting.schemas import (
    AuditEventSummary,
    DashboardStatsResponse,
    ProjectSummary,
    TaskCountsByStatus,
)
from app.shared.database import get_session
from app.shared.errors import NotFound

router = APIRouter(tags=["dashboard"])


@router.get(
    "/dashboard/stats",
    response_model=DashboardStatsResponse,
    summary="Get dashboard statistics",
    description="Get aggregated dashboard statistics including project count, task counts, and recent activity.",
)
def get_dashboard_stats(
    project_id: str | None = None,
    session: Session = Depends(get_session),  # noqa: B008
) -> DashboardStatsResponse:
    """Get aggregated dashboard statistics."""
    service = DashboardService(session)
    stats = service.get_stats(project_id=project_id)
    return DashboardStatsResponse(
        project_count=stats["project_count"],
        task_counts_by_status=TaskCountsByStatus(**stats["task_counts_by_status"]),
        recent_projects=[ProjectSummary(**p) for p in stats["recent_projects"]],
        recent_activity=[AuditEventSummary(**a) for a in stats["recent_activity"]],
        done_this_week=stats["done_this_week"],
        blocked_count=stats["blocked_count"],
        claimed_count=stats["claimed_count"],
        health_score=stats["health_score"],
    )


@router.get(
    "/dashboard/attention",
    summary="Get attention dashboard",
    description="Get action items requiring user attention such as blocked tasks and overdue items.",
)
def get_dashboard_attention(
    project_id: str | None = None,
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, object]]]:  # noqa: B008
    """Get attention dashboard — action items requiring user attention."""
    svc = AttentionDashboardService(session)
    return svc.get_attention(project_id=project_id)


@router.get(
    "/projects/{project_id}/health",
    summary="Get project health score",
    description="Get the health score and detailed breakdown for a specific project.",
    responses={404: {"description": "Project not found"}},
)
def get_project_health(
    project_id: str,
    session: Session = Depends(get_session),
) -> dict[str, object]:  # noqa: B008
    """Get project health score with breakdown.

    Unknown projects raise ``NotFound`` (→ 404) — the documented contract.
    Existing projects keep the computed score, including the score-100
    default when they have no tasks (TASK-0087).
    """
    if session.get(Project, project_id) is None:
        raise NotFound(f"Project '{project_id}' not found")
    svc = AttentionDashboardService(session)
    return svc.get_project_health(project_id)


@router.get(
    "/portfolio/overview",
    summary="Get portfolio overview",
    description="Get a portfolio-level overview with summaries across all projects.",
)
def get_portfolio_overview(
    session: Session = Depends(get_session),
) -> dict[str, object]:  # noqa: B008
    """Get portfolio-level overview with project summaries."""
    svc = PortfolioService(session)
    return svc.get_overview()


@router.get(
    "/dashboard/agent-activity",
    summary="Get agent activity",
    description="Get active agents with their current task, progress percentage, and heartbeat status.",
)
def get_agent_activity(
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, object]]]:  # noqa: B008
    """Get active agents with current task, progress, and heartbeat status."""
    svc = DashboardService(session)
    return {"items": svc.active_agents()}
