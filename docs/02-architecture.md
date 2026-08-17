# Architecture

UPCP is a modular monolith.

> **Source of truth for bounded contexts**: `docs/architecture/ddd-contexts.md`
> **Source of truth for data model**: `docs/architecture/data-model.md`

## Backend

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- PostgreSQL
- Alembic
- Typer CLI
- MCP server

## Frontend

- React
- TypeScript
- Vite
- Tailwind
- shadcn/ui
- TanStack Query
- TanStack Router
- TanStack Table

## Core modules

```text
backend/app/
  shared/
  health/
  projects/
  structure/
  delivery/
  quality/
  gitread/
  reporting/
  llm/
  audit/
  mcp/
  api/
```

## External integrations

- Git providers: local Git, GitHub, GitLab
- CI: read-only status consumption
- LLM: optional, via `llm/gateway.py` (redaction layer for secrets). UPCP does NOT call LLM providers directly — agents interact via MCP clients (Cursor, Claude, Qwen Code) which handle their own LLM calls.
- Prometheus/Grafana: optional observability (behind `observability` Docker profile)

## Important constraint

UPCP does not modify project code repositories.

It may:

- read branches;
- read commits;
- read pull requests;
- read checks;
- link Git objects to tasks.

It must not:

- push commits;
- create branches;
- open PRs;
- modify files in project repositories.
