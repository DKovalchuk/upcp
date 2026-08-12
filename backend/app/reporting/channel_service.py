import logging
from typing import Any

from sqlalchemy.orm import Session

from app.reporting.channels import get_channel
from app.reporting.models import Notification, NotificationChannel, NotificationDelivery
from app.shared.errors import NotFound, ValidationError
from app.shared.text import new_id, utcnow

logger = logging.getLogger(__name__)


class ChannelService:
    def __init__(self, session: Session) -> None:
        self._session = session

    # ── CRUD ──────────────────────────────────────────────────

    def create(self, channel_type: str, name: str, config: dict[str, Any]) -> NotificationChannel:
        if channel_type not in ("email", "webhook"):
            raise ValidationError(f"Invalid channel type: {channel_type}")
        ch = get_channel(channel_type)
        ch.validate_config(config)

        channel = NotificationChannel(
            id=new_id(),
            channel_type=channel_type,
            name=name,
            config=config,
            is_active=True,
        )
        self._session.add(channel)
        self._session.commit()
        return channel

    def list_all(self) -> list[NotificationChannel]:
        return (
            self._session.query(NotificationChannel)
            .order_by(NotificationChannel.created_at.desc())
            .all()
        )

    def get(self, channel_id: str) -> NotificationChannel:
        ch = self._session.get(NotificationChannel, channel_id)
        if not ch:
            raise NotFound(f"Channel {channel_id} not found")
        return ch

    def delete(self, channel_id: str) -> None:
        ch = self.get(channel_id)
        self._session.delete(ch)
        self._session.commit()

    def toggle_active(self, channel_id: str) -> NotificationChannel:
        ch = self.get(channel_id)
        ch.is_active = not ch.is_active
        self._session.commit()
        return ch

    # ── Dispatch ──────────────────────────────────────────────

    def send_notification(self, notification: Notification) -> None:
        """Send a notification through all active channels."""
        channels = (
            self._session.query(NotificationChannel)
            .filter(NotificationChannel.is_active == True)  # noqa: E712
            .all()
        )
        for ch in channels:
            delivery = NotificationDelivery(
                id=new_id(),
                notification_id=notification.id,
                channel_id=ch.id,
                status="pending",
            )
            self._session.add(delivery)
            self._session.flush()

            try:
                impl = get_channel(ch.channel_type)
                impl.send(ch.config, notification.title, notification.message)
                delivery.status = "sent"
                delivery.sent_at = utcnow()
            except Exception as exc:
                logger.warning("Channel %s delivery failed: %s", ch.id, exc)
                delivery.status = "failed"
                delivery.error_message = str(exc)

        self._session.commit()

    def test_channel(self, channel_id: str) -> bool:
        """Send a test notification through a specific channel."""
        ch = self.get(channel_id)
        impl = get_channel(ch.channel_type)
        impl.send(ch.config, "UPCP Test", "This is a test notification from UPCP.")
        return True
