"""Analytics API routes — TASK-0102."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.reporting.analytics import AnalyticsService
from app.shared.database import get_session
from app.shared.pagination import PaginationParams, pagination_dependency

router = APIRouter(tags=["analytics"])


@router.get(
    "/analytics/velocity",
    summary="Global tasks completed per week",
)
def global_velocity(
    weeks: int = Query(default=8, ge=1, le=52),
    project_id: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, Any]]]:
    svc = AnalyticsService(session)
    return {"items": svc.get_global_velocity(weeks, project_id)}


@router.get(
    "/analytics/project/{project_id}/trends",
    summary="Project task trends over time",
)
def project_trends(
    project_id: str,
    weeks: int = Query(default=8, ge=1, le=52),
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, Any]]]:
    svc = AnalyticsService(session)
    return {"items": svc.get_project_trends(project_id, weeks)}


@router.get(
    "/analytics/project/{project_id}/velocity",
    summary="Tasks completed per week",
)
def project_velocity(
    project_id: str,
    weeks: int = Query(default=8, ge=1, le=52),
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, Any]]]:
    svc = AnalyticsService(session)
    return {"items": svc.get_team_velocity(project_id, weeks)}


@router.get(
    "/analytics/project/{project_id}/health-history",
    summary="Health score over time",
)
def health_history(
    project_id: str,
    days: int = Query(default=30, ge=1, le=365),
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, Any]]]:
    svc = AnalyticsService(session)
    return {"items": svc.get_health_history(project_id, days)}


@router.get(
    "/analytics/agent/{agent_id}/performance",
    summary="Agent performance metrics",
)
def agent_performance(
    agent_id: str,
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, Any]]]:
    svc = AnalyticsService(session)
    return {"items": svc.get_agent_performance(agent_id)}


@router.get(
    "/analytics/agents/overview",
    summary="All agents summary",
)
def agents_overview(
    pagination: PaginationParams = Depends(pagination_dependency),  # noqa: B008
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    svc = AnalyticsService(session)
    items, total = svc.get_agents_overview(limit=pagination.limit, offset=pagination.offset)
    return {
        "items": items,
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }
