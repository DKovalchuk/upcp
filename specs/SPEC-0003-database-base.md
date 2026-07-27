# SPEC-0003 Database Base and Migrations

Status: approved
Owner: project-owner
Milestone: M0
Related tasks: TASK-0003

## Problem

No database engine, session, or migration infrastructure exists.

## Goal

Provide:

- SQLAlchemy engine and session factory (async-ready, but sync for now);
- Declarative Base model;
- Alembic configured with auto-generation;
- Initial empty migration.

## Non-goals

- No domain models yet (M1+).
- No async sessions (can add later).
- No connection pooling tuning.

## Requirements

1. Engine reads `DATABASE_URL` from Settings.
2. `get_session()` provides a DB session.
3. `Base` is a declarative base for all models.
4. Alembic `alembic.ini` + `alembic/` configured.
5. Alembic `env.py` uses same engine/session.
6. Initial migration is empty (just sets up Alembic).
7. Unit tests don't require running PostgreSQL.

## Acceptance Criteria

- `database.py` provides `engine`, `SessionLocal`, `Base`, `get_session()`.
- Alembic init succeeds, `alembic.ini` exists.
- `alembic/` directory with `env.py` and `script.py.mako` exist.
- Initial migration generated.
- `make test` passes (unit tests, no DB required).
- `make lint` passes.
- `make typecheck` passes.

## Risks

- Alembic auto-gen needs a running DB — initial empty migration avoids this.

## DoD

- Spec approved.
- Task implemented with TDD.
- All commands pass.
- Statuses updated.
