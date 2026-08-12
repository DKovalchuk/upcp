"""In-process event bus for decoupled cross-context communication.

Services publish events; handlers subscribe to specific event types.
Replaces direct NotificationTrigger calls throughout the codebase.
"""

import contextlib
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class EventBus:
    """Simple synchronous in-process event bus."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[..., Any]) -> None:
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[..., Any]) -> None:
        with contextlib.suppress(ValueError):
            self._handlers[event_type].remove(handler)

    def publish(self, event_type: str, **kwargs: Any) -> None:
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event_type=event_type, **kwargs)
            except Exception:
                logger.warning(
                    "Event handler failed for '%s': %s",
                    event_type,
                    handler.__qualname__,
                    exc_info=True,
                )

    def clear(self) -> None:
        self._handlers.clear()


event_bus = EventBus()
