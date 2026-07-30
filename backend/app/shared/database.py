import time
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.shared.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_health() -> dict[str, object]:
    """Check database connectivity by executing SELECT 1.

    Returns:
        dict with status "ok" and latency_ms on success,
        or status "error" and error message on failure.
    """
    try:
        start = time.monotonic()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = (time.monotonic() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency_ms, 2)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
