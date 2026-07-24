# UPCP

Universal Project Control Plane.

Self-hosted, local-first, open-source-friendly control plane for multi-project engineering management.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React + TypeScript + Vite + Tailwind + shadcn/ui
- Agent interface: MCP, REST API, CLI
- Docs: markdown-first
- Deployment: Docker Compose

## Local Ports

Default external ports are intentionally non-standard:

| Service     | External Port |
|-------------|---------------:|
| App/API/UI  | 38080 |
| PostgreSQL  | 35432 |
| Prometheus  | 39090 |
| Grafana     | 33000 |
| Frontend dev| 35173 |

## Quick Start

```bash
cp .env.example .env
make install
make test
make up
```

App health:

```bash
curl http://127.0.0.1:38080/health
```

## Agent Docs

Start here:

```text
AGENTS.md
docs/INDEX.md
PROJECT_STATUS.md
tasks/
specs/
```
