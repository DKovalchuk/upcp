"""Reaper endpoint — POST /internal/reaper/tick (superuser-only since TASK-0172).

TASK-0099 (B2); RBAC (TASK-0172 inventory): internal ops endpoint that
mutates claim state — the background loop drives the service directly and
no non-admin HTTP caller exists (tests/e2e/scripts), so the route carries
``require_superuser``.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.delivery.stale_reaper import reaper_tick
from app.identity.permissions import require_superuser
from app.shared.database import get_session

router = APIRouter(tags=["reaper"])


@router.post(
    "/internal/reaper/tick",
    summary="Trigger stale claim reaper",
    description="Run one pass of stale claim detection and auto-release.",
    dependencies=[Depends(require_superuser())],
)
def reaper_tick_endpoint(
    session: Session = Depends(get_session),
) -> dict[str, int]:
    return reaper_tick(session)
