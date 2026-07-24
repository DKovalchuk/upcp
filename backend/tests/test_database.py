import contextlib

from app.shared.database import Base, SessionLocal, engine, get_session
from sqlalchemy.orm import Session


def test_engine_is_created() -> None:
    assert engine.url.drivername in ("postgresql", "postgresql+psycopg")


def test_base_is_declarative() -> None:
    assert hasattr(Base, "metadata")


def test_session_local_is_callable() -> None:
    session = SessionLocal()
    assert isinstance(session, Session)
    session.close()


def test_get_session_yields_session() -> None:
    gen = get_session()
    session = next(gen)
    assert isinstance(session, Session)
    with contextlib.suppress(StopIteration):
        gen.close()


def test_alembic_ini_exists() -> None:
    from pathlib import Path

    ini = Path(__file__).resolve().parents[2] / "alembic.ini"
    assert ini.exists(), f"alembic.ini not found at {ini}"


def test_alembic_env_exists() -> None:
    from pathlib import Path

    env = Path(__file__).resolve().parents[1] / "alembic" / "env.py"
    assert env.exists(), f"alembic/env.py not found at {env}"


def test_initial_migration_exists() -> None:
    from pathlib import Path

    versions = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    if versions.exists():
        files = list(versions.glob("*.py"))
        assert len(files) >= 1, "No migration files found"
    else:
        raise AssertionError("alembic/versions directory not found")


def test_base_metadata_tables_empty() -> None:
    tables = Base.metadata.tables.keys()
    assert len(list(tables)) == 0 or all(
        t.startswith("alembic_") for t in tables
    )
