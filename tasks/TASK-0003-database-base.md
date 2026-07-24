# TASK-0003 Database Base and Migrations

Spec: SPEC-0003
Status: done
Priority: 10
Model: routine
Milestone: M0

## Goal

Set up SQLAlchemy engine, session, Base model, and Alembic migrations.

## Non-goals

- No domain models.
- No async sessions.

## Files likely involved

```text
backend/app/shared/database.py
backend/alembic.ini
backend/alembic/env.py
backend/alembic/script.py.mako
backend/alembic/versions/0001_initial.py
backend/tests/test_database.py
```

## TDD Steps

1. Create failing tests for database module.
2. Run tests, confirm failure.
3. Implement database.py.
4. Initialize Alembic.
5. Generate initial migration.
6. Run tests, confirm pass.
7. Run lint and typecheck.

## Acceptance Criteria

- `engine` created from `DATABASE_URL`.
- `SessionLocal` factory.
- `Base` declarative base.
- `get_session()` yields session.
- Alembic configured.
- Initial migration exists.
- `make test`, `make lint`, `make typecheck` pass.
- Statuses updated.

## DoD

- tests added;
- implementation added;
- Alembic configured;
- commands pass;
- statuses updated.
