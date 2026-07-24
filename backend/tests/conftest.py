from collections.abc import Generator

from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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


def make_test_app(*routers: object) -> FastAPI:
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    app = FastAPI()
    register_error_handlers(app)
    for router in routers:
        app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    return app
