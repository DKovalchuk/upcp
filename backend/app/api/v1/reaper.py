"""Reaper endpoint — POST /internal/reaper/tick.

TASK-0099 (B2)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.delivery.stale_reaper import reaper_tick
from app.shared.database import get_session

router = APIRouter(tags=["reaper"])


@router.post(
    "/internal/reaper/tick",
    summary="Trigger stale claim reaper",
    description="Run one pass of stale claim detection and auto-release.",
)
def reaper_tick_endpoint(
    session: Session = Depends(get_session),
) -> dict[str, int]:
    return reaper_tick(session)
