"""AgentTokenService — single agent-token verification path (SPEC-0029 §3.4 / TASK-0174).

Removes the duplication of ``middleware.py``'s agent branch and
``agent_auth.get_current_agent`` (D4 outcome parity):

- one ``sha256`` helper (AC5 — the duplicated ``_hash_token`` copies
  disappear when consumers are rewired in TASK-0170/0175);
- lifecycle: unknown hash / revoked / expired / agent missing / agent
  inactive → ``verify_detailed`` returns the reason (TASK-0175 — the
  dependency maps it to its historical 401 strings) while ``verify``
  folds every reason to ``None`` (the middleware still distinguishes its
  detail strings itself until TASK-0170);
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
from typing import Literal

from app.identity.repositories import AgentRepository, AgentTokenRepository

AgentTokenRejectionReason = Literal["unknown", "revoked", "expired", "agent_inactive"]


@dataclass(frozen=True, slots=True)
class AgentPrincipal:
    """Authenticated agent identity — mirrors ``dependencies.CurrentAgent``."""

    agent_id: str
    name: str
    scopes: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class AgentTokenRejection:
    """Rejection with its reason — the ADDITIVE detail API (TASK-0175).

    Consumers map reasons onto their historical 401 detail strings
    (byte-parity); ``verify`` folds every reason into ``None``.
    """

    reason: AgentTokenRejectionReason


def _hash_token(token: str) -> str:
    """The ONE sha256 of the raw agent token (AC5 — TASK-0175 removes the
    ``agent_auth`` copy; ``middleware`` keeps its own until TASK-0170)."""
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

    def verify_detailed(
        self, raw_token: str, now: datetime | None = None
    ) -> AgentPrincipal | AgentTokenRejection:
        """Lifecycle checks with an explicit rejection reason + committed touch.

        Rejection paths do NOT touch the token (parity: middleware and
        agent_auth only stamp ``last_used_at`` on success); DB errors
        propagate — repositories never swallow them. ``verify`` is the
        thin ``None``-folding wrapper over this method.
        """
        current = _ensure_utc(now) if now is not None else datetime.now(UTC)

        record = self._tokens.find_by_hash(_hash_token(raw_token))
        if record is None:
            return AgentTokenRejection("unknown")
        if record.revoked_at is not None:
            return AgentTokenRejection("revoked")
        if record.expires_at is not None and _ensure_utc(record.expires_at) < current:
            return AgentTokenRejection("expired")

        agent = self._agents.get(record.agent_id)
        if agent is None or not agent.is_active:
            return AgentTokenRejection("agent_inactive")

        scopes = record.scopes  # capture before the touch's commit
        # commit-before-response (service.py / TASK-0142) — see docstring
        self._tokens.touch_last_used(record, current)
        return AgentPrincipal(agent_id=agent.id, name=agent.name, scopes=scopes)

    def verify(self, raw_token: str, now: datetime | None = None) -> AgentPrincipal | None:
        """Lifecycle checks + single committed ``last_used_at`` touch.

        Every rejection folds to ``None`` (consumers that do not need the
        reason); implemented as a wrapper over ``verify_detailed`` (AC5:
        one verification implementation).
        """
        result = self.verify_detailed(raw_token, now)
        return result if isinstance(result, AgentPrincipal) else None
