# UPCP — Universal Project Control Plane

[English](README.md) | [Русский](README.ru.md)

![CI](https://github.com/DKovalchuk/upcp/actions/workflows/ci.yml/badge.svg)

**Self-hosted, local-first control plane for multi-project engineering management — with AI agents as first-class contributors.**

UPCP gives a team (and its AI agents) a single place to plan work, drive it
through a governed workflow, attach evidence, and prove quality before
anything ships. Humans stay in control: agents propose, humans review and
accept.

## Contents

- [Why UPCP](#why-upcp)
- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Quality and testing](#quality-and-testing)
- [Agent-driven development](#agent-driven-development)
- [Quick start](#quick-start)
- [Repository map](#repository-map)
- [Documentation](#documentation)
- [CI/CD](#cicd)
- [License](#license)

## Why UPCP

Engineering teams drown in project trackers that were built for humans
clicking boxes. AI agents can now do real work — but they need structured
interfaces, verifiable evidence, and review gates, not tickets with a
"blocked" label.

UPCP is built the other way around:

- **Work is a state machine.** Tasks move through a defined lifecycle
  (`backlog → ready → claimed → in_progress → ready_for_review → done`, plus
  blocked/clarification/cancel paths). Invalid transitions are rejected by
  the API, not by convention.
- **Claims are leases.** Agents claim work explicitly, heartbeat to prove
  liveness, and a reaper releases stale claims automatically — no silent
  double-assignment.
- **Quality is evidence-based.** Definition-of-done checklists, acceptance
  criteria, uploaded evidence, review rounds with findings, and a hard gate
  that blocks completion until checks pass.
- **Everything is auditable.** Every transition, claim, review, and gate
  decision lands in an append-only audit trail and feeds dashboards.

## Features

- **Project structure** — projects → components → modules → features → tasks,
  with memberships and role-based access control (RBAC).
- **Task workflow engine** — full lifecycle with server-side transition
  validation, bulk operations, dependencies, comments, and subtasks.
- **Agent workflow** — agent registration, scoped tokens, claims with
  heartbeats, clarifications (agents can ask humans; blocking questions stop
  the clock), and a stale-claim reaper.
- **Quality management** — Definition of Done, acceptance criteria, evidence
  with verification states, review rounds (human and agent reviewers),
  findings with severity, completion gates.
- **Reporting and analytics** — attention boards, velocity, health history,
  quality statistics, CSV exports; notification channels (in-app, email,
  webhook) with SSE push to the UI.
- **Interfaces** — REST API (OpenAPI), **MCP server** for AI agents, CLI,
  and a React SPA.
- **Observability** — structured logs, OpenTelemetry traces, Prometheus
  metrics, and a bundled Grafana/Loki/Tempo stack behind a Docker profile.
- **Git integration (read-only)** — branches and commits linked to projects
  for context, never mutation.

## Architecture

Modular monolith, domain-driven: a FastAPI application organized around
bounded contexts with explicit service/schema/repository boundaries and
Alembic-managed migrations.

```text
                       ┌──────────────────────────────────────────┐
   Browser ───────────▶│  React SPA (TanStack Router/Query, UI)   │
                       └────────────────┬─────────────────────────┘
                                        │ REST + SSE
   AI agents ── MCP ───┐               │
   CLI ────────────────┤               ▼
                       │      ┌─────────────────────┐     ┌─────────────┐
                       └─────▶│  FastAPI backend     │────▶│ PostgreSQL  │
                              │  ┌────────────────┐  │     └─────────────┘
                              │  │ api   mcp      │  │     ┌─────────────┐
                              │  │ projects  structure  │◀───│ Redis       │
                              │  │ delivery  quality│  │     └─────────────┘
                              │  │ gitread  reporting│ │
                              │  │ llm  audit  shared │ │     ┌─────────────┐
                              │  └────────────────┘  │────▶│ OTel → Tempo │
                              └─────────────────────┘     │ Prom → Grafana│
                                                           └─────────────┘
```

Bounded contexts: `projects`, `structure`, `delivery`, `quality`, `gitread`,
`reporting`, `notifications`, `llm`, `audit`, `mcp`, `api`, `shared`,
`health`. See [`docs/architecture/ddd-contexts.md`](docs/architecture/ddd-contexts.md)
and [`docs/INDEX.md`](docs/INDEX.md).

## Tech stack

| Layer | Choices |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL 16, Redis 7 |
| Frontend | React 19, TypeScript, Vite, TanStack Router/Query, Tailwind, shadcn/ui, Recharts |
| Agent interface | MCP (JSON-RPC 2.0), REST/OpenAPI, CLI |
| Observability | OpenTelemetry, Prometheus, Grafana, Loki, Tempo |
| Quality tooling | pytest, ruff, mypy, Playwright (e2e), ZAP + Kali (security), Locust (load), chaos suite |
| Deployment | Docker Compose, Nginx, GitLab CI |

## Quality and testing

| Signal | Value |
|---|---|
| Backend tests | **1,102** tests collected in 108 files |
| Frontend tests | 57 test suites (Vitest) |
| Extra suites | e2e (Playwright), security (ZAP baseline + Kali + authz/fuzz), chaos, load (Locust), lighthouse |
| Coverage gate | ≥ 80 % (`make coverage`) |
| Static checks | ruff, mypy (strict), tsc, oxlint |
| Process docs | 29 specs, 140+ task files with acceptance criteria and evidence |

CI runs `lint → test → quality → build → deploy`; the quality gate is a hard
gate (a red gate blocks deploys) and covers the security/chaos/perf suites.

## Agent-driven development

This repository is also a case study in operating AI coding agents:

- [`AGENTS.md`](AGENTS.md) — operating manual for agents: reading order,
  token-economy rules, DDD boundaries, mandatory TDD, stop conditions,
  Definition of Done, multi-factor review.
- **Spec Flow → TDD** — every non-trivial change goes spec → task → failing
  test → implementation; specs live in [`specs/`](specs/), tasks (with AC and
  evidence) in [`tasks/`](tasks/).
- **Model routing** — cheapest-sufficient model for routine work, escalation
  rules for architecture/security work.
- **Evidence discipline** — tasks are only closed with passing tests, CI
  evidence, and a multi-factor analysis attached to the task file.
- [`PROJECT_STATUS.md`](PROJECT_STATUS.md) and [`ROADMAP_UNIFIED.md`](ROADMAP_UNIFIED.md)
  track milestone state; [`CHANGELOG.md`](CHANGELOG.md) records releases.

Over 600 commits across the development branches (382 on the released
`main` line) were produced under this workflow — task branches, merge
requests, quality gates, and human review on every merge.

## Quick start

```bash
git clone https://github.com/DKovalchuk/upcp.git
cd upcp

cp .env.example .env          # defaults are fine for local dev
make install                  # venv + backend deps
make test                     # backend test suite

docker compose up --build     # full stack (app, db, redis, frontend)
```

Health check:

```bash
curl http://127.0.0.1:38080/health
```

Ports are intentionally non-standard and configured through `.env.*` files
(dev 3072/38080, test 3071/38082, stage 3070/38081) — see
[`docs/11-docker-and-ports.md`](docs/11-docker-and-ports.md). For the stage
stack, create `.env.stage` from `.env.stage.example` first.

## Repository map

```text
backend/          FastAPI app: bounded contexts, models, services, API, MCP
frontend/         React SPA (Vite + Tailwind + shadcn/ui)
tests/            Cross-cutting suites: e2e, security, chaos, performance, quality gate
specs/             Gherkin specs (SPEC-XXXX)
tasks/            Task files with AC, evidence, and closure notes (TASK-XXXX)
docs/             Architecture, processes, ops, PRD — indexed in docs/INDEX.md
scripts/          Dev/ops tooling: seeding, verification, public export
observability/    Prometheus/Grafana/Loki/Tempo configuration
```

## Documentation

Start with [`docs/INDEX.md`](docs/INDEX.md) — it maps every document to the
situation where you would read it. Key entry points:

- [`docs/00-vision.md`](docs/00-vision.md) — product vision
- [`docs/02-architecture.md`](docs/02-architecture.md) — system architecture
- [`docs/architecture/agent-workflow-state-machine.md`](docs/architecture/agent-workflow-state-machine.md) — workflow semantics
- [`docs/ENVIRONMENTS.md`](docs/ENVIRONMENTS.md) — local environments and credentials

## CI/CD

Pipelines run on every merge request and on the main branches: lint, type
check, unit/integration tests, dependency and container scans, the composite
quality gate, container builds, and environment deploys. Release branches are
cut into `main`, which is what this public mirror publishes.

## License

[MIT](LICENSE)
