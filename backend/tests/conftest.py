"""Shared test fixtures for UPCP backend tests.

All models are imported here so Base.metadata.create_all() knows about every table.
Test files should use the `db_session` fixture instead of creating their own engines.
"""

import os
from collections.abc import Generator

# Disable auth and rate limiting in tests via explicit flags (not env="test")
os.environ.setdefault("UPCP_DISABLE_AUTH", "true")
os.environ.setdefault("UPCP_DISABLE_RATE_LIMIT", "true")

# ── All imports after env setup (E402 suppressed) ─────────────
import app.delivery.models  # noqa: E402, F401
import app.gitread.models  # noqa: E402, F401
import app.identity.agents  # noqa: E402, F401
import app.identity.models  # noqa: E402, F401
import app.identity.rbac  # noqa: E402, F401
import app.projects.models  # noqa: E402, F401
import app.quality.models  # noqa: E402, F401
import app.reporting.models  # noqa: E402, F401
import app.structure.models  # noqa: E402, F401
import pytest  # noqa: E402
from app.shared.database import Base, get_session  # noqa: E402
from app.shared.errors import register_error_handlers  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402


def _set_sqlite_pragma(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
event.listen(_test_engine, "connect", _set_sqlite_pragma)
_TestSession = sessionmaker(bind=_test_engine)


def _override_session() -> Generator:
    s = _TestSession()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Fresh hermetic DB per test: recreate schema, roll back on teardown.

    TASK-0112 folded the local per-file ``sqlite:///:memory:`` engines
    into this shared engine; drop+create preserves the per-test
    freshness those fixtures had (commits on the shared StaticPool
    connection would otherwise leak between tests).
    """
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    session = _TestSession()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


def make_test_app(*routers: object) -> FastAPI:
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    app = FastAPI()
    register_error_handlers(app)
    for router in routers:
        app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    return app


@pytest.fixture(autouse=True)
def _redirect_session_local(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hermetic tests must not resolve the compose-only ``db`` host.

    AuthMiddleware resolves ``SessionLocal`` lazily per request
    (SPEC-0027 §3.2 user-existence check); the process DATABASE_URL points
    at a host that is unreachable (or foreign) from the test runner, so
    middleware user lookups must land on the shared in-memory test DB.
    Live suites under ``tests/security/`` use their own conftest and keep
    the real factory.
    """
    import app.shared.database as db_mod

    monkeypatch.setattr(db_mod, "SessionLocal", _TestSession)


@pytest.fixture()
def seed_subject() -> Generator:
    """Create an active user row for a minted JWT subject; removed after the test.

    SPEC-0027 §3.2: a valid signature alone no longer authenticates — the
    subject must exist, so tests minting fixed subs (``user-123``) seed a
    matching row *after* any ``make_test_app()`` (which drops tables).
    """
    created: list[str] = []

    def _seed(user_id: str) -> str:
        from app.identity.models import User

        Base.metadata.create_all(bind=_test_engine)
        session = _TestSession()
        try:
            session.merge(
                User(
                    id=user_id,
                    email=f"{user_id}@middleware.test",
                    password_hash="x" * 60,
                    display_name="Middleware Subject",
                )
            )
            session.commit()
        finally:
            session.close()
        created.append(user_id)
        return user_id

    yield _seed
    session = _TestSession()
    try:
        from app.identity.models import User

        for user_id in created:
            session.query(User).filter_by(id=user_id).delete()
        session.commit()
    finally:
        session.close()
