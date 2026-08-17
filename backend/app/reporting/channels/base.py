from abc import ABC, abstractmethod
from typing import Any


class BaseChannel(ABC):
    """Abstract base for notification channel implementations."""

    @abstractmethod
    def send(self, config: dict[str, Any], title: str, message: str) -> None:
        """Send a notification via this channel.

        Args:
            config: Channel-specific configuration (e.g. SMTP settings, webhook URL).
            title: Notification title.
            message: Notification body.

        Raises:
            Exception: On delivery failure.
        """

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> None:
        """Validate channel configuration.

        Raises:
            ValueError: If config is invalid.
        """
