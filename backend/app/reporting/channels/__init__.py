from app.reporting.channels.base import BaseChannel
from app.reporting.channels.email import EmailChannel
from app.reporting.channels.webhook import WebhookChannel

CHANNEL_MAP: dict[str, type[BaseChannel]] = {
    "email": EmailChannel,
    "webhook": WebhookChannel,
}


def get_channel(channel_type: str) -> BaseChannel:
    cls = CHANNEL_MAP.get(channel_type)
    if not cls:
        raise ValueError(f"Unknown channel type: {channel_type}")
    return cls()
