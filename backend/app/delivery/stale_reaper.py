"""Stale claim reaper — detect and release dead agent claims.

TASK-0099 (B2)

Runs as asyncio background task AND exposes POST /internal/reaper/tick.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.delivery.inbox_events import create_agent_event
from app.delivery.lifecycle import validate_transition
from app.delivery.models import Task, TaskClaim
from app.shared.events import event_bus

logger = logging.getLogger(__name__)

STALE_MINUTES = 5
DEAD_MINUTES = 15


def reaper_tick(session: Session) -> dict[str, int]:
    """Run one reaper pass. Returns counts of stale notifications and dead releases."""
    stale_count = 0
    released_count = 0

    now = datetime.now(UTC)
    stale_cutoff = now - timedelta(minutes=STALE_MINUTES)
    dead_cutoff = now - timedelta(minutes=DEAD_MINUTES)

    # Find active claims that are stale but not yet dead
    stale_claims = (
        session.query(TaskClaim)
        .filter(TaskClaim.state == "active")
        .filter(TaskClaim.last_heartbeat_at.isnot(None))
        .filter(TaskClaim.last_heartbeat_at < stale_cutoff)
        .filter(TaskClaim.last_heartbeat_at >= dead_cutoff)
        .all()
    )

    for claim in stale_claims:
        create_agent_event(
            session,
            agent_id=claim.agent_id,
            event_type="heartbeat_stale",
            task_id=claim.task_id,
            message=f"Claim on task {claim.task_id} is stale (no heartbeat for >{STALE_MINUTES}min)",
        )
        task = session.get(Task, claim.task_id)
        event_bus.publish(
            "claim.stale",
            session=session,
            entity_type="task",
            entity_id=claim.task_id,
            actor_id="system",
            metadata={
                "agent_id": claim.agent_id,
                "task_title": task.title if task else claim.task_id,
            },
        )
        stale_count += 1

    # Find active claims that are dead (no heartbeat for > DEAD_MINUTES)
    # Include claims never heartbeated that were claimed long ago
    dead_claims = (
        session.query(TaskClaim)
        .filter(TaskClaim.state == "active")
        .filter(
            (TaskClaim.last_heartbeat_at.isnot(None) & (TaskClaim.last_heartbeat_at < dead_cutoff))
            | (TaskClaim.last_heartbeat_at.is_(None) & (TaskClaim.claimed_at < dead_cutoff))
        )
        .all()
    )

    for claim in dead_claims:
        claim.state = "released"
        claim.released_at = now

        task = session.get(Task, claim.task_id)
        if task is not None:
            try:
                validate_transition(task.status, "backlog")
                task.status = "backlog"
            except Exception:
                logger.warning(
                    "Cannot release claim %s: task %s in state '%s'",
                    claim.id,
                    claim.task_id,
                    task.status if task else "unknown",
                )
                continue

        create_agent_event(
            session,
            agent_id=claim.agent_id,
            event_type="claim_released",
            task_id=claim.task_id,
            message=f"Claim on task {claim.task_id} auto-released (no heartbeat for >{DEAD_MINUTES}min)",
        )
        released_count += 1

    if stale_count or released_count:
        session.flush()

    return {"stale": stale_count, "released": released_count}


async def stale_reaper_loop(
    session_factory: Callable[[], Session], interval_seconds: int = 60
) -> None:
    """Background asyncio loop that runs reaper_tick periodically."""
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            with session_factory() as session:
                result = reaper_tick(session)
                if result["stale"] or result["released"]:
                    logger.info(
                        "Reaper tick: %d stale, %d released",
                        result["stale"],
                        result["released"],
                    )
        except Exception:
            logger.exception("Reaper tick failed")
