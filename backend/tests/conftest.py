from collections.abc import Generator

import pytest
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from fastapi import FastAPI
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


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
    """Provide a transactional DB session that rolls back after each test."""
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
