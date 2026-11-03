"""Identity repositories — the only DB access in the auth path (SPEC-0029 D1/S29.1).

Layering pilot (TASK-0174): middleware/dependencies stop querying
``SessionLocal`` directly — data access lives here and nowhere else in
the identity auth path (AC1). Two seams per D3:

- constructor-injected ``session`` (unit tests, request-scoped DI);
- session-less → ``SessionLocal`` resolved LAZILY inside each method
  (the ``middleware._fetch_user_state`` test-seam precedent — tests
  redirect ``app.shared.database.SessionLocal``).

Session-less calls open ONE session per call and always close it.
``touch_last_used`` is the single write point for ``last_used_at`` and
COMMITS before returning (commit-before-response invariant —
``identity/service.py`` / TASK-0142: flush-only races the client's next
request). This resolves the middleware-``commit()`` vs
agent_auth-``flush()`` divergence in favour of commit (AC4).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.identity.agents import Agent, AgentToken
from app.identity.models import User


class UserRepository:
    """Subject-state lookup — mirrors ``middleware._fetch_user_state``."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def get_auth_state(self, user_id: str) -> str:
        """Subject lookup → ``"active" | "unknown" | "disabled"``."""
        if self._session is not None:
            return self._auth_state(self._session, user_id)
        from app.shared.database import SessionLocal  # lazy — test seam (D3)

        db = SessionLocal()
        try:
            return self._auth_state(db, user_id)
        finally:
            db.close()

    @staticmethod
    def _auth_state(db: Session, user_id: str) -> str:
        user = db.get(User, user_id)
        if user is None:
            return "unknown"
        return "active" if user.is_active else "disabled"


class AgentTokenRepository:
    """Agent-token lookup + the single ``last_used_at`` write point (AC4)."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def find_by_hash(self, token_hash: str) -> AgentToken | None:
        """Row for ``token_hash`` or ``None`` (unknown hash → reject)."""
        if self._session is not None:
            return self._find_by_hash(self._session, token_hash)
        from app.shared.database import SessionLocal  # lazy — test seam (D3)

        db = SessionLocal()
        try:
            return self._find_by_hash(db, token_hash)
        finally:
            db.close()

    def touch_last_used(self, record: AgentToken, when: datetime) -> None:
        """Stamp ``last_used_at`` and COMMIT before returning.

        Commit-before-response (service.py / TASK-0142): a flush-only
        write races the client's next request. Written by primary key so
        it works for both an injected (attached) and a session-less
        (detached, loaded) record.
        """
        if self._session is not None:
            self._touch(self._session, record, when)
            return
        from app.shared.database import SessionLocal  # lazy — test seam (D3)

        db = SessionLocal()
        try:
            self._touch(db, record, when)
        finally:
            db.close()

    @staticmethod
    def _find_by_hash(db: Session, token_hash: str) -> AgentToken | None:
        return db.query(AgentToken).filter_by(token_hash=token_hash).first()

    @staticmethod
    def _touch(db: Session, record: AgentToken, when: datetime) -> None:
        (
            db.query(AgentToken)
            .filter_by(id=record.id)
            .update({"last_used_at": when}, synchronize_session=False)
        )
        db.commit()


class AgentRepository:
    """Agent row lookup — the active/lifecycle check belongs to the service."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def get(self, agent_id: str) -> Agent | None:
        if self._session is not None:
            return self._session.get(Agent, agent_id)
        from app.shared.database import SessionLocal  # lazy — test seam (D3)

        db = SessionLocal()
        try:
            return db.get(Agent, agent_id)
        finally:
            db.close()
