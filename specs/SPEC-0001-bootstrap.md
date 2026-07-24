# SPEC-0001 Bootstrap Repository and Health

Status: approved
Owner: project-owner
Milestone: M0
Related tasks: TASK-0001

## Problem

The project needs a reliable starting point with agent-friendly documentation, Docker setup, testing foundation, and a minimal backend health endpoint.

## Goal

Create a repository scaffold that allows:

- local development;
- Docker Compose startup;
- health check;
- test execution;
- lint execution;
- typecheck execution;
- future backend expansion.

## Non-goals

- no database tables yet;
- no auth;
- no UI;
- no MCP server;
- no Git integration;
- no LLM integration.

## Requirements

1. Backend must expose `GET /health`.
2. Health endpoint must return JSON:

```json
{
  "status": "ok",
  "service": "upcp-backend"
}
```

3. Docker Compose must expose app on external port `38080` by default.
4. PostgreSQL must expose external port `35432` by default.
5. Tests must run with `make test`.
6. Lint must run with `make lint`.
7. Typecheck must run with `make typecheck`.
8. No secrets may be committed.

## Acceptance Criteria

- `make test` passes.
- `make lint` passes.
- `make typecheck` passes.
- `docker compose config` validates.
- App starts and `GET /health` returns expected payload.
- External ports are non-standard and configurable via `.env`.

## DoD

- scaffold exists;
- health test exists;
- health endpoint exists;
- Docker config valid;
- docs updated;
- PROJECT_STATUS updated.
