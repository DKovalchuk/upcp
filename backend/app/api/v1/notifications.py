"""Notification API routes — TASK-0085."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.reporting.service import NotificationService
from app.reporting.sse import sse_manager
from app.shared.database import get_session
from app.shared.errors import NotFound

router = APIRouter(tags=["notifications"])


@router.get(
    "/notifications",
    summary="List notifications",
    description="List all notifications for a user, optionally filtering to unread only.",
)
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


@router.get(
    "/notifications/unread-count",
    summary="Get unread notification count",
    description="Get the count of unread notifications for a user.",
)
def unread_count(
    user_id: str = "default",
    session: Session = Depends(get_session),
) -> dict[str, int]:  # noqa: B008
    svc = NotificationService(session)
    return {"count": svc.unread_count(user_id)}


@router.post(
    "/notifications/{notification_id}/read",
    summary="Mark a notification as read",
    description="Mark a specific notification as read.",
    responses={404: {"description": "Notification not found"}},
)
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


@router.post(
    "/notifications/read-all",
    summary="Mark all notifications as read",
    description="Mark all notifications for a user as read.",
)
def mark_all_read(
    user_id: str = "default",
    session: Session = Depends(get_session),
) -> dict[str, int]:  # noqa: B008
    svc = NotificationService(session)
    count = svc.mark_all_read(user_id)
    return {"count": count}


@router.get(
    "/notifications/stream",
    summary="SSE stream for real-time notifications",
    description="Server-Sent Events stream. Sends keepalive every 15s.",
)
async def notifications_stream() -> StreamingResponse:
    client_id, queue = sse_manager.connect()

    async def event_generator():  # type: ignore[no-untyped-def]
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15)
                    yield message
                except TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            sse_manager.disconnect(client_id)

    return StreamingResponse(
        event_generator(),  # type: ignore[no-untyped-call]
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
