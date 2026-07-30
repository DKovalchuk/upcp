"""Notification API routes — TASK-0085."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.reporting.service import NotificationService
from app.shared.database import get_session
from app.shared.errors import NotFound

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
def list_notifications(
    user_id: str = "default",
    unread_only: bool = False,
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, str | bool | None]]]:  # noqa: B008
    svc = NotificationService(session)
    items = svc.list_by_user(user_id, unread_only=unread_only)
    return {
        "items": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "entity_type": n.entity_type,
                "entity_id": n.entity_id,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ]
    }


@router.get("/notifications/unread-count")
def unread_count(
    user_id: str = "default",
    session: Session = Depends(get_session),
) -> dict[str, int]:  # noqa: B008
    svc = NotificationService(session)
    return {"count": svc.unread_count(user_id)}


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str | bool | None]:  # noqa: B008
    svc = NotificationService(session)
    try:
        n = svc.mark_read(notification_id)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    return {
        "id": n.id,
        "is_read": n.is_read,
    }


@router.post("/notifications/read-all")
def mark_all_read(
    user_id: str = "default",
    session: Session = Depends(get_session),
) -> dict[str, int]:  # noqa: B008
    svc = NotificationService(session)
    count = svc.mark_all_read(user_id)
    return {"count": count}
