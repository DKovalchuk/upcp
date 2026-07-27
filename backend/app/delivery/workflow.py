"""Agent workflow service — claim, release, heartbeat, progress.

TASK-0074
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.delivery.lifecycle import validate_transition
from app.delivery.models import Heartbeat, Task, TaskClaim
from app.shared.errors import Conflict, NotFound
from app.shared.text import new_id


class WorkflowService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def claim(
        self,
        task_id: str,
        *,
        agent_id: str,
        context_snapshot: str | None = None,
    ) -> TaskClaim:
        """Claim a ready task for an agent."""
        task = self._session.get(Task, task_id)
        if task is None:
            raise NotFound(f"task '{task_id}' not found")

        if task.status != "ready":
            raise Conflict(f"task is '{task.status}', must be 'ready' to claim")

        existing = self._session.query(TaskClaim).filter_by(task_id=task_id, state="active").first()
        if existing is not None:
            raise Conflict("task is already claimed")

        claim = TaskClaim(
            id=new_id(),
            task_id=task_id,
            agent_id=agent_id,
            state="active",
            context_snapshot=context_snapshot,
        )
        self._session.add(claim)
        validate_transition(task.status, "claimed")
        task.status = "claimed"
        self._session.flush()
        return claim

    def release(self, task_id: str, *, agent_id: str) -> None:
        """Release an agent's claim on a task."""
        task = self._session.get(Task, task_id)
        if task is None:
            raise NotFound(f"task '{task_id}' not found")

        claim = self._session.query(TaskClaim).filter_by(task_id=task_id, state="active").first()
        if claim is None:
            raise NotFound("no active claim on this task")

        if claim.agent_id != agent_id:
            raise Conflict("only the claiming agent can release")

        claim.state = "released"
        claim.released_at = datetime.now(UTC)
        validate_transition(task.status, "backlog")
        task.status = "backlog"
        self._session.flush()

    def heartbeat(
        self,
        task_id: str,
        *,
        agent_id: str,
        progress_percent: int,
        current_step: str,
        next_step: str,
        blockers: str | None = None,
        eta: str | None = None,
    ) -> Heartbeat:
        """Send a heartbeat on a claimed task."""
        claim = self._get_active_claim(task_id, agent_id)

        hb = Heartbeat(
            id=new_id(),
            claim_id=claim.id,
            progress_percent=progress_percent,
            current_step=current_step,
            next_step=next_step,
            blockers=blockers,
            eta=eta,
        )
        self._session.add(hb)
        claim.last_heartbeat_at = datetime.now(UTC)
        self._session.flush()
        return hb

    def progress(
        self,
        task_id: str,
        *,
        agent_id: str,
        progress_percent: int,
    ) -> Heartbeat:
        """Update progress on a claimed task."""
        claim = self._get_active_claim(task_id, agent_id)

        hb = Heartbeat(
            id=new_id(),
            claim_id=claim.id,
            progress_percent=progress_percent,
            current_step="",
            next_step="",
        )
        self._session.add(hb)
        claim.last_heartbeat_at = datetime.now(UTC)
        self._session.flush()
        return hb

    def _get_active_claim(self, task_id: str, agent_id: str) -> TaskClaim:
        """Get active claim, verifying ownership."""
        claim = self._session.query(TaskClaim).filter_by(task_id=task_id, state="active").first()
        if claim is None:
            raise NotFound("no active claim on this task")
        if claim.agent_id != agent_id:
            raise Conflict("not your claim")
        return claim
