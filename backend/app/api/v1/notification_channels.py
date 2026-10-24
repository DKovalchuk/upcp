"""Notification channel API routes — TASK-0101."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.reporting.channel_service import ChannelService
from app.reporting.models import NotificationChannel
from app.shared.database import get_session
from app.shared.errors import NotFound, ValidationError

router = APIRouter(tags=["notification-channels"])


class ChannelCreate(BaseModel):
    channel_type: str
    name: str
    config: dict[str, Any] = {}


class ChannelUpdate(BaseModel):
    name: str | None = None
    config: dict[str, Any] | None = None


class ChannelResponse(BaseModel):
    id: str
    channel_type: str
    name: str
    config: dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str


def _to_response(ch: NotificationChannel) -> dict[str, Any]:
    return {
        "id": ch.id,
        "channel_type": ch.channel_type,
        "name": ch.name,
        "config": ch.config,
        "is_active": ch.is_active,
        "created_at": ch.created_at.isoformat() if ch.created_at else "",
        "updated_at": ch.updated_at.isoformat() if ch.updated_at else "",
    }


@router.get(
    "/notification-channels",
    summary="List notification channels",
)
def list_channels(
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, Any]]]:
    svc = ChannelService(session)
    channels = svc.list_all()
    return {"items": [_to_response(ch) for ch in channels]}


@router.post(
    "/notification-channels",
    summary="Create a notification channel",
    status_code=201,
)
def create_channel(
    body: ChannelCreate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    svc = ChannelService(session)
    try:
        ch = svc.create(body.channel_type, body.name, body.config)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return _to_response(ch)


@router.patch(
    "/notification-channels/{channel_id}",
    summary="Update a notification channel",
)
def update_channel(
    channel_id: str,
    body: ChannelUpdate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    svc = ChannelService(session)
    try:
        ch = svc.update(channel_id, name=body.name, config=body.config)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return _to_response(ch)


@router.delete(
    "/notification-channels/{channel_id}",
    summary="Delete a notification channel",
)
def delete_channel(
    channel_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    svc = ChannelService(session)
    try:
        svc.delete(channel_id)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    return {"status": "deleted"}


@router.post(
    "/notification-channels/{channel_id}/toggle",
    summary="Toggle channel active state",
)
def toggle_channel(
    channel_id: str,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    svc = ChannelService(session)
    try:
        ch = svc.toggle_active(channel_id)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    return _to_response(ch)


@router.post(
    "/notification-channels/{channel_id}/test",
    summary="Send a test notification through a channel",
)
def test_channel(
    channel_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    svc = ChannelService(session)
    try:
        svc.test_channel(channel_id)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Test failed: {exc}") from None
    return {"status": "sent"}
