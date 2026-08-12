"""Server-Sent Events manager for real-time notifications.

Manages connected SSE clients and broadcasts events to them.
"""

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class SSEManager:
    """Manages SSE client connections and broadcasts events."""

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[str | None]] = {}
        self._counter = 0

    def connect(self) -> tuple[str, asyncio.Queue[str | None]]:
        """Register a new SSE client. Returns (client_id, queue)."""
        self._counter += 1
        client_id = f"sse-{self._counter}"
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._queues[client_id] = queue
        logger.info("SSE client connected: %s (total: %d)", client_id, len(self._queues))
        return client_id, queue

    def disconnect(self, client_id: str) -> None:
        """Remove an SSE client."""
        self._queues.pop(client_id, None)
        logger.info("SSE client disconnected: %s (total: %d)", client_id, len(self._queues))

    def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast an event to all connected clients.

        Non-blocking: drops events for clients with full queues.
        """
        payload = json.dumps(data)
        message = f"event: {event_type}\ndata: {payload}\n\n"
        stale: list[str] = []
        for client_id, queue in self._queues.items():
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                stale.append(client_id)
        for cid in stale:
            self._queues.pop(cid, None)
            logger.warning("SSE client %s dropped (queue full)", cid)

    @property
    def client_count(self) -> int:
        return len(self._queues)


# Module-level singleton
sse_manager = SSEManager()
