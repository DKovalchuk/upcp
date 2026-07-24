# Architecture

UPCP is a modular monolith.

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
- LLM: optional assistant layer
- Prometheus/Grafana: optional observability

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
