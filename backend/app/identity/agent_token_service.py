"""AgentTokenService — single agent-token verification path (SPEC-0029 §3.4 / TASK-0174).

Removes the duplication of ``middleware.py``'s agent branch and
``agent_auth.get_current_agent`` (D4 outcome parity):

- one ``sha256`` helper (AC5 — the duplicated ``_hash_token`` copies
  disappear when consumers are rewired in TASK-0170/0175);
- lifecycle: unknown hash / revoked / expired / agent missing / agent
  inactive → ``None`` (consumers map ``None`` to their existing 401
  shapes; the middleware still distinguishes its detail strings until
  TASK-0170);
- expiry is a strict ``<`` against an injectable ``now`` (middleware
  semantics: ``expires_at == now`` still verifies); tz-naive stored
  values are read as UTC — SQLite drops the offset (prod Postgres
  round-trips unchanged), which previously raised ``TypeError``
  (middleware → generic 401, agent dependency → 500) on SQLite;
- WRITE SEMANTICS (documented decision): the service COMMITS via
  ``AgentTokenRepository.touch_last_used`` after every successful
  verification — commit-before-response (``identity/service.py`` /
  TASK-0142: flush-only races the client's next request). This resolves
  the existing divergence — middleware ``commit()`` vs agent_auth
  ``flush()`` — in favour of commit (AC4).

DB errors propagate (repositories never swallow); the middleware
consumer must keep mapping them to its fail-closed 401 as it does today.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from app.identity.repositories import AgentRepository, AgentTokenRepository


@dataclass(frozen=True, slots=True)
class AgentPrincipal:
    """Authenticated agent identity — mirrors ``dependencies.CurrentAgent``."""

    agent_id: str
    name: str
    scopes: dict[str, object] | None = None


def _hash_token(token: str) -> str:
    """The ONE sha256 of the raw token (AC5 — dedupes middleware/agent_auth)."""
    return hashlib.sha256(token.encode()).hexdigest()


def _ensure_utc(value: datetime) -> datetime:
    """Tz-naive values (SQLite round-trip) are UTC wall time."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class AgentTokenService:
    """Verify raw ``X-Agent-Token`` values into principals, or ``None``."""

    def __init__(
        self,
        agent_token_repository: AgentTokenRepository,
        agent_repository: AgentRepository,
    ) -> None:
        self._tokens = agent_token_repository
        self._agents = agent_repository

    def verify(self, raw_token: str, now: datetime | None = None) -> AgentPrincipal | None:
        """Lifecycle checks + single committed ``last_used_at`` touch.

        Rejection paths do NOT touch the token (parity: middleware and
        agent_auth only stamp ``last_used_at`` on success).
        """
        current = _ensure_utc(now) if now is not None else datetime.now(UTC)

        record = self._tokens.find_by_hash(_hash_token(raw_token))
        if record is None or record.revoked_at is not None:
            return None

        if record.expires_at is not None and _ensure_utc(record.expires_at) < current:
            return None

        agent = self._agents.get(record.agent_id)
        if agent is None or not agent.is_active:
            return None

        scopes = record.scopes  # capture before the touch's commit
        # commit-before-response (service.py / TASK-0142) — see docstring
        self._tokens.touch_last_used(record, current)
        return AgentPrincipal(agent_id=agent.id, name=agent.name, scopes=scopes)
