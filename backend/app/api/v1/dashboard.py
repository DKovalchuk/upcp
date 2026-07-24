"""Dashboard API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.reporting.dashboard import DashboardService
from app.reporting.schemas import DashboardStatsResponse
from app.shared.database import get_session

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(session: Session = Depends(get_session)) -> DashboardStatsResponse:  # noqa: B008
    """Get aggregated dashboard statistics."""
    service = DashboardService(session)
    stats = service.get_stats()
    return DashboardStatsResponse(**stats)