#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path

FILES: dict[str, str] = {}

FILES["AGENTS.md"] = r'''
# AGENTS.md — UPCP AI Agent Operating Rules

This file is the primary operating manual for AI coding agents.

It must be treated as a stable cached prefix.
Do not rewrite this file during routine tasks.

## 1. Prime Directive

You are working on UPCP — Universal Project Control Plane.

You must always optimize for:

1. Correctness.
2. Small reversible changes.
3. Token efficiency.
4. Test evidence.
5. Clear traceability.
6. Production-grade habits from day one.

You are not allowed to:

- implement large features without a task file;
- add production code without a failing test, except pure scaffolding;
- silently change architecture, public API, DB schema, auth, or security;
- dump whole repositories into context;
- store secrets in code, docs, logs, tests, or prompts;
- mark a task done without evidence.

## 2. Mandatory Reading Order

For any task, read only what is necessary.

Default order:

1. This file: `AGENTS.md`
2. `PROJECT_STATUS.md`
3. Current task file: `tasks/TASK-XXXX-*.md`
4. Related spec file: `specs/SPEC-XXXX-*.md`
5. Only then, if blocked:
   - relevant docs from `docs/INDEX.md`
   - only the specific files needed for implementation

Do not read all docs.
Do not read all source files.
Use search and targeted reads.

## 3. Token Economy Rules

These rules are mandatory.

### 3.1 Context discipline

- Keep active context as small as possible.
- Prefer reading interfaces, schemas, tests, and error messages.
- Do not read entire files if only a symbol is needed.
- Use `rg`, `ls`, `find`, or equivalent search tools first.
- Read a file only if you must modify it or need its contract.
- Prefer small diffs over full file rewrites.
- Do not paste long logs; truncate to the relevant 30–50 lines.
- Do not repeat large context in answers.

### 3.2 File size discipline

- Markdown docs should usually be <= 250 lines.
- Code files should usually be <= 300 lines.
- Test files should usually be <= 300 lines.
- If a file grows too large, create a refactor task.
- Do not perform large refactors inside a feature task unless explicitly required.

### 3.3 Cache-friendly behavior

This project assumes models with prefix caching, including:

- MiMo-V2.5
- DeepSeek-V4 Flash
- Pro variants for audit/critical work

To benefit from cache:

- Keep `AGENTS.md` stable.
- Keep core docs stable.
- Put dynamic data at the end of prompts.
- Do not reorder stable docs.
- Do not rename docs frequently.
- Use stable IDs: `SPEC-xxxx`, `TASK-xxxx`, `UPC-Fxx`, `UPC-xxx`.
- Use small task files instead of huge combined prompts.

### 3.4 Task context pack

For routine implementation, prefer this context shape:

```text
AGENTS.md              stable
current task file      dynamic
related spec           only if needed
interface snippets     only if needed
failing test output    truncated
```

Avoid:

```text
all docs
all source files
full docker files
full dependency tree
long history
```

## 4. Spec Flow

Every non-trivial change starts with a spec.

Flow:

```text
Idea
→ Spec
→ Optional Design
→ Task decomposition
→ Failing tests
→ Implementation
→ Verification
→ Review
→ Done
```

Rules:

- A feature must have a spec file in `specs/`.
- A task must reference a spec or parent task.
- Small tasks may use the task file as a mini-spec.
- Critical changes require a full spec and Pro-level review.
- If requirements are unclear, stop and create a clarification task.

## 5. DDD Rules

UPCP is a modular monolith organized by bounded contexts.

Main contexts:

```text
health
shared
projects
structure      # components, modules
delivery       # features, tasks
quality        # DoD, acceptance criteria
gitread        # read-only git integration
reporting
llm
audit
mcp
api
```

Rules:

- Respect context boundaries.
- Do not import internal implementation details from another context.
- Prefer explicit services, schemas, and repositories.
- Keep domain logic pure where practical.
- Keep infrastructure adapters separate.
- Avoid cross-context direct DB joins in early tasks unless explicitly allowed.
- Use ubiquitous language from docs.

## 6. TDD Rules

TDD is mandatory for behavior-changing code.

Cycle:

```text
Red
→ Green
→ Refactor
```

Rules:

- Write a failing test first.
- Implement the minimum code to pass.
- Refactor only after tests pass.
- Do not add speculative abstractions.
- Every bugfix must start with a regression test.
- Scaffolding files may be created without tests, but must be validated by a smoke test or command.
- Do not mark done without passing tests.

## 7. Definition of Done

A task is done only if:

- acceptance criteria are satisfied;
- failing test existed before implementation, where applicable;
- tests pass;
- lint passes;
- type check passes where configured;
- docs affected by the change are updated;
- no secrets are introduced;
- task file status is updated;
- `PROJECT_STATUS.md` is updated;
- evidence is available: test output, command output, or artifact.

## 8. Model Routing

Use the cheapest sufficient model.

Routine models:

- MiMo-V2.5
- DeepSeek-V4 Flash

Use routine models for:

- small tasks;
- CRUD;
- tests;
- docs;
- simple bugfixes;
- refactors with clear tests;
- UI component tweaks;
- repetitive implementation.

Use Pro models for:

- architecture review;
- security review;
- DB schema changes;
- auth/RBAC changes;
- public API contract changes;
- DDD boundary changes;
- complex debugging after two failed routine attempts;
- critical migrations;
- LLM redaction/security logic;
- audit after milestone completion.

If a routine model fails twice on the same issue, stop and either:

1. decompose the task; or
2. escalate to Pro model.

## 9. Stop Conditions

Stop and report if:

- task is ambiguous;
- required context is missing;
- change touches security, auth, permissions, or secrets;
- DB migration is required;
- public API contract must change;
- tests cannot be written;
- context budget is exceeded;
- more than two failed fix attempts occur;
- a file is too large and needs decomposition.

## 10. Output Discipline

Final response must be concise.

Prefer:

```text
Summary
Files changed
Tests added
Commands run
Evidence
Next task
Blockers
```

Do not output entire files unless explicitly requested.
Do not output long explanations unless debugging.
'''

FILES["QWEN.md"] = r'''
# QWEN.md

Read and follow `AGENTS.md`.

If there is any conflict between other documents and `AGENTS.md`, `AGENTS.md` wins for agent behavior.

For current project state, read `PROJECT_STATUS.md`.

For current work, read the active task in `tasks/`.
'''

FILES["README.md"] = r'''
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
'''

FILES["PROJECT_STATUS.md"] = r'''
# PROJECT_STATUS

Updated: 2026-07-24
Milestone: M0
Current Task: TASK-0001
Next Task: TASK-0002
Blockers: none

## Last Result

Repository scaffold and agent docs created.
Waiting for TASK-0001 implementation.

## Important Notes

- Use non-standard Docker ports.
- Use TDD.
- Keep context small.
- Read `AGENTS.md` before any task.
'''

FILES["docs/INDEX.md"] = r'''
# Documentation Index

Read only what is needed for the current task.

| Doc | Purpose | Read when |
|---|---|---|
| `00-vision.md` | Product vision | Starting a new feature or milestone |
| `01-principles.md` | Engineering principles | Making trade-offs |
| `02-architecture.md` | System architecture | Creating modules or services |
| `03-domain-model.md` | Entities and relationships | Changing data model |
| `04-spec-flow.md` | Spec workflow | Creating specs/tasks |
| `05-ddd.md` | Domain boundaries | Adding contexts/modules |
| `06-tdd.md` | Testing workflow | Writing code |
| `07-token-economy.md` | Token-saving rules | Prompting agents |
| `08-coding-standards.md` | Code style and limits | Writing or reviewing code |
| `09-testing-standards.md` | Test structure | Writing tests |
| `10-git-conventions.md` | Branches/commits | Committing work |
| `11-docker-and-ports.md` | Docker ports | Running locally |
| `12-bootstrap-plan.md` | Milestones and first tasks | Planning implementation |
| `13-model-routing.md` | Light vs Pro model usage | Choosing model |
| `decisions.md` | Append-only decisions | Recording assumptions |
'''

FILES["docs/00-vision.md"] = r'''
# UPCP Vision

UPCP is a universal project control plane for owners, AI agents, reviewers, and automation.

It provides:

- multi-project portfolio control;
- structured context for AI agents;
- traceability from vision to commit;
- DoD-based quality control;
- read-only Git integration;
- reporting and observability;
- MCP/API/CLI interfaces.

Primary focus for v1:

- software engineering projects;
- small teams and single owners;
- self-hosted laptop deployment;
- agent-assisted development;
- production-grade habits without enterprise bloat.
'''

FILES["docs/01-principles.md"] = r'''
# Engineering Principles

1. Small reversible changes.
2. Explicit contracts over magic.
3. Tests before behavior.
4. Evidence before Done.
5. Read-only Git integration for project repositories.
6. Secrets never enter docs, logs, prompts, or LLM context.
7. Token-efficient context over maximal context.
8. Modular monolith first.
9. Deterministic core; LLM only as assistant.
10. Human owner keeps final authority.
'''

FILES["docs/02-architecture.md"] = r'''
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
'''

FILES["docs/03-domain-model.md"] = r'''
# Domain Model

Core entities:

```text
Project
Component
Module
Feature
Task
AcceptanceCriterion
DoDItem
Spec
GitRepo
GitBranch
GitCommit
GitPullRequest
GitLink
AuditEvent
Report
User
Agent
Role
Permission
```

Primary structural hierarchy:

```text
Project
└── Component
    └── Module
```

Primary delivery hierarchy:

```text
Project
└── Feature
    └── Task
        └── Subtask
```

Flexible links:

```text
Feature
  -> primary_component
  -> linked_components
  -> linked_modules

Task
  -> feature
  -> component
  -> module
  -> git links
```

Optional DDD layer:

```text
Project
└── Domain/Area
    └── Component
        └── Module
```
'''

FILES["docs/04-spec-flow.md"] = r'''
# Spec Flow

All non-trivial work follows Spec Flow.

```text
Idea
→ Spec
→ Optional Design
→ Tasks
→ Failing Tests
→ Implementation
→ Verification
→ Review
→ Done
```

## Spec file

Location:

```text
specs/SPEC-XXXX-short-name.md
```

Minimum spec content:

```markdown
# SPEC-XXXX

Status: draft | review | approved
Owner:
Related features:
Related tasks:

## Problem

## Goal

## Non-goals

## Requirements

## Acceptance Criteria

## Risks

## DoD
```

## Task file

Location:

```text
tasks/TASK-XXXX-short-name.md
```

Minimum task content:

```markdown
# TASK-XXXX

Spec:
Status: backlog | ready | in_progress | blocked | done
Priority:
Model: routine | pro

## Goal

## Non-goals

## Files

## Acceptance Criteria

## Tests

## DoD

## Notes
```

## Rules

- No large feature without spec.
- No implementation task without tests.
- No Done without DoD.
- Unclear task → clarification task.
'''

FILES["docs/05-ddd.md"] = r'''
# DDD Rules

UPCP uses bounded contexts inside a modular monolith.

## Contexts

```text
health
shared
projects
structure
delivery
quality
gitread
reporting
llm
audit
mcp
api
```

## Context responsibilities

### health

Liveness/readiness endpoints.

### shared

Cross-cutting utilities:

- config;
- logging;
- errors;
- pagination;
- ids;
- time.

### projects

Project lifecycle and metadata.

### structure

Components and modules.

### delivery

Features, tasks, subtasks.

### quality

Acceptance criteria and DoD.

### gitread

Read-only Git provider integration.

### reporting

Daily/weekly/portfolio reports.

### llm

Optional LLM gateway and redaction.

### audit

Immutable audit events.

### mcp

MCP tools and resources.

### api

HTTP routers and API composition.

## Dependency rules

```text
interfaces -> application/services -> domain
infrastructure -> application interfaces
```

Avoid:

- direct import of internal details from another context;
- cross-context tight coupling;
- shared mutable state;
- god services.
'''

FILES["docs/06-tdd.md"] = r'''
# TDD Rules

TDD is mandatory for behavior-changing code.

## Cycle

```text
1. Write failing test.
2. Run test and confirm failure.
3. Write minimal implementation.
4. Run test and confirm pass.
5. Refactor if needed.
6. Run lint/typecheck/tests.
```

## Test types

- unit tests: pure logic, services, validators;
- integration tests: API + DB;
- smoke tests: app starts, health works;
- acceptance tests: user-visible behavior.

## Rules

- No production behavior without failing test.
- Bugfix requires regression test.
- Do not test implementation details.
- Prefer testing public contracts.
- Use fixtures for repeated setup.
- Keep tests deterministic.
- Avoid network calls in unit tests.
- Use fakes for time, randomness, external services.

## Evidence

A task must include at least one of:

- pytest output;
- make test output;
- curl smoke output;
- docker compose validation output.
'''

FILES["docs/07-token-economy.md"] = r'''
# Token Economy Rules

This project is designed for efficient work with:

- MiMo-V2.5
- DeepSeek-V4 Flash
- Pro variants for audit/critical tasks

## Core idea

Do not maximize context.
Minimize sufficient context.

## Prompt structure

Preferred stable prefix:

```text
AGENTS.md
selected stable docs
task template
```

Dynamic suffix:

```text
current task
current status
specific error
specific interface snippet
```

## Context budgets

Approximate targets:

| Work type | Active context target |
|---|---:|
| routine implementation | <= 15k–25k tokens |
| debugging | <= 30k–40k tokens |
| architecture audit | Pro model, curated context |
| full milestone review | Pro model, curated context |

These are targets, not hard limits.

## Mandatory habits

- read only required files;
- use search before reading;
- avoid whole-file dumps;
- avoid whole-repo dumps;
- truncate logs;
- keep files small;
- keep docs small;
- use stable IDs;
- use task files;
- use small diffs;
- do not repeat large text in answers;
- prefer examples over long prose;
- prefer typed contracts over implicit behavior.

## Cache-aware rules

For models with prefix caching:

- keep `AGENTS.md` stable;
- keep core docs stable;
- avoid renaming files often;
- avoid reordering stable docs;
- append decisions instead of rewriting;
- put volatile data last.

## When to stop and decompose

Stop if:

- more than 6 files must be held in active context;
- a file is too large;
- logs exceed useful size;
- the task requires cross-context refactoring;
- the model fails twice on the same issue.

Then create smaller subtasks.
'''

FILES["docs/08-coding-standards.md"] = r'''
# Coding Standards

## Python

- Python 3.12.
- Strict typing.
- Pydantic schemas for API input/output.
- Small modules.
- One responsibility per module.
- Explicit error handling.
- Structured logging.
- No secrets in code.
- No print statements in app code.
- Use `logging` or structured logger.
- Prefer pure functions where practical.
- Avoid deep inheritance.
- Avoid global mutable state.

## File limits

- code file: usually <= 300 lines;
- test file: usually <= 300 lines;
- markdown doc: usually <= 250 lines.

## Naming

- English identifiers.
- snake_case for functions/variables.
- PascalCase for classes.
- UPPER_SNAKE_CASE for constants.
- stable task/spec IDs in docs and commits.

## API

- versioned under `/api/v1`;
- JSON responses;
- explicit schemas;
- pagination for lists;
- problem-like error responses;
- idempotency keys for mutating operations where needed.

## Errors

Use typed error taxonomy:

```text
validation_error
not_found
permission_denied
conflict
dod_failed
approval_required
external_git_error
external_ci_error
internal_error
```

## Logging

Log structured events:

```text
event
project_id
entity_type
entity_id
actor_type
actor_id
error_code
```

Do not log:

- secrets;
- tokens;
- passwords;
- full LLM prompts by default;
- sensitive personal data.
'''

FILES["docs/09-testing-standards.md"] = r'''
# Testing Standards

## Test naming

```text
test_<behavior>_<condition>_<expected>
```

Examples:

```python
test_health_returns_ok
test_create_project_with_duplicate_slug_fails
test_task_done_fails_when_dod_not_passed
```

## Test structure

Use Arrange-Act-Assert.

```python
def test_example() -> None:
    # arrange
    ...

    # act
    ...

    # assert
    ...
```

## Pyramid

```text
unit tests       70%
integration      20%
e2e/smoke        10%
```

## Rules

- tests must be deterministic;
- no real network calls in unit tests;
- no real secrets;
- use fixtures;
- use in-memory or test DB for integration;
- truncate long outputs;
- prefer fast feedback.

## Commands

```bash
make test
make lint
make typecheck
```
'''

FILES["docs/10-git-conventions.md"] = r'''
# Git Conventions

## Branch naming

```text
task/UPC-<task_number>-short-slug
feature/UPC-F<feature_number>-short-slug
fix/UPC-<task_number>-short-slug
docs/UPC-<task_number>-short-slug
chore/UPC-<task_number>-short-slug
```

Examples:

```text
task/UPC-1-scaffold-health
feature/UPC-F1-bootstrap
fix/UPC-12-health-timeout
```

## Commit format

```text
<type>(<scope>): <summary> [UPC-<task_number>]
```

Examples:

```text
chore(repo): scaffold project [UPC-1]
test(health): add health smoke test [UPC-1]
feat(health): add health endpoint [UPC-1]
docs(agents): clarify token economy [UPC-1]
```

## Rules

- one task per branch where practical;
- one logical change per commit;
- no secrets in commits;
- no generated artifacts in commits;
- do not push automatically unless explicitly allowed;
- do not modify remote project repositories from UPCP runtime.
'''

FILES["docs/11-docker-and-ports.md"] = r'''
# Docker and Ports

External ports are intentionally non-standard.

| Service | Internal Port | External Default | Env Variable |
|---|---:|---:|---|
| App/API/UI | 8080 | 38080 | `UPCP_HTTP_PORT` |
| PostgreSQL | 5432 | 35432 | `UPCP_POSTGRES_PORT` |
| Prometheus | 9090 | 39090 | `UPCP_PROMETHEUS_PORT` |
| Grafana | 3000 | 33000 | `UPCP_GRAFANA_PORT` |
| Frontend dev | 5173 | 35173 | `UPCP_FRONTEND_DEV_PORT` |

Rules:

- external services bind to `127.0.0.1` by default;
- do not expose services to LAN unless explicitly needed;
- internal container ports may remain standard;
- if a port conflicts, change only the external port in `.env`.

Observability services are optional and use Docker profile:

```bash
docker compose --profile observability up
```
'''

FILES["docs/12-bootstrap-plan.md"] = r'''
# Bootstrap Plan

## Milestone M0 — Repository and Health

Goal:

- repository scaffold;
- docker compose;
- backend health endpoint;
- basic tests;
- basic lint/typecheck;
- docs for agents.

Tasks:

```text
TASK-0001 scaffold repo and health endpoint
TASK-0002 config, logging, error foundation
TASK-0003 database base and migrations foundation
TASK-0004 audit event append-only model
```

## Milestone M1 — Core Project Model

Goal:

- project CRUD;
- project list;
- project status;
- basic RBAC placeholders;
- API schemas.

## Milestone M2 — Structure and Delivery

Goal:

- components;
- modules;
- features;
- tasks;
- subtasks;
- acceptance criteria;
- DoD items.

## Milestone M3 — Git Read Integration

Goal:

- Git provider config;
- local Git read adapter;
- GitHub read adapter;
- GitLab read adapter;
- branch/commit/PR links.

## Milestone M4 — MCP and CLI

Goal:

- MCP server;
- context packs;
- task tools;
- project tools;
- CLI.

## Milestone M5 — Rich UI

Goal:

- React app;
- portfolio;
- project dashboard;
- task board;
- task deep dive;
- quality view.

## Milestone M6 — Reports and Optional LLM

Goal:

- daily report;
- markdown export;
- optional LLM summary;
- LLM redaction.
'''

FILES["docs/13-model-routing.md"] = r'''
# Model Routing

Use the cheapest sufficient model.

## Routine models

Use:

- MiMo-V2.5
- DeepSeek-V4 Flash

For:

- small implementation tasks;
- tests;
- docs;
- simple bugfixes;
- small refactors;
- UI component work;
- repetitive CRUD;
- validation logic;
- report templates.

## Pro models

Use Pro variants for:

- architecture review;
- security review;
- DB schema changes;
- migrations;
- auth/RBAC;
- permission model;
- secret handling;
- LLM redaction;
- public API contract changes;
- DDD boundary changes;
- performance issues;
- complex debugging;
- milestone audit.

## Escalation rules

Escalate to Pro if:

- routine model fails twice on same issue;
- task touches critical modules;
- context is too large for routine model;
- change is irreversible;
- security or data integrity is involved.

## Critical modules

These require Pro review:

```text
auth
permissions
audit
db migrations
secret handling
LLM redaction
API contract changes
quality gate logic
```
'''

FILES["docs/decisions.md"] = r'''
# Decisions

Append-only.
Keep this file under 100 lines.
Archive old decisions when needed.

## Format

```text
YYYY-MM-DD | DEC-xxxx | decision | reason
```

## Decisions

2026-07-24 | DEC-0001 | Use Python FastAPI backend | Best balance for AI tooling, typing, MCP, and team preference
2026-07-24 | DEC-0002 | Use React rich frontend | Product requires rich functional UI
2026-07-24 | DEC-0003 | Use non-standard Docker ports | Standard ports are occupied on host
2026-07-24 | DEC-0004 | Use English machine docs | Better token efficiency and code-model performance
2026-07-24 | DEC-0005 | UPCP runtime is read-only for project Git repos | Safety and owner requirement
'''

FILES["specs/SPEC-0001-bootstrap.md"] = r'''
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
'''

FILES["tasks/TASK-0001-scaffold-health.md"] = r'''
# TASK-0001 Scaffold Repository and Health Endpoint

Spec: SPEC-0001
Status: ready
Priority: 10
Model: routine
Milestone: M0

## Goal

Create the minimal backend health endpoint and validate the repository scaffold.

## Non-goals

- Do not add database models.
- Do not add auth.
- Do not add frontend.
- Do not add MCP.
- Do not add LLM.
- Do not add Git integration.

## Files likely involved

```text
backend/app/__init__.py
backend/app/main.py
backend/tests/__init__.py
backend/tests/test_health.py
```

## TDD Steps

1. Create failing test `backend/tests/test_health.py`.
2. Run test and confirm failure.
3. Create minimal `backend/app/main.py`.
4. Run test and confirm pass.
5. Run lint and typecheck.
6. Validate Docker Compose.
7. Optionally start app and check health.

## Expected test

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "upcp-backend",
    }
```

## Expected implementation

```python
from fastapi import FastAPI

app = FastAPI(title="UPCP Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "upcp-backend",
    }
```

## Acceptance Criteria

- failing test exists before implementation;
- `GET /health` returns expected payload;
- `make test` passes;
- `make lint` passes;
- `make typecheck` passes;
- `docker compose config` succeeds;
- no secrets are added;
- task status updated;
- PROJECT_STATUS updated.

## Commands

```bash
make test
make lint
make typecheck
docker compose config
cp .env.example .env
docker compose up --build
curl http://127.0.0.1:38080/health
```

## DoD

- test added;
- endpoint added;
- commands pass;
- status updated.
'''

FILES["prompts/00-initial-qwen-prompt.md"] = r'''
You are Qwen CLI working inside the UPCP repository.

Your job is to implement the current task using Spec Flow, DDD, and TDD.

Follow `AGENTS.md` strictly.

Do not read all documentation.
Do not read all source files.
Do not implement anything outside the current task.

Current task:

```text
tasks/TASK-0001-scaffold-health.md
```

Allowed context:

```text
AGENTS.md
PROJECT_STATUS.md
tasks/TASK-0001-scaffold-health.md
specs/SPEC-0001-bootstrap.md
backend/app/__init__.py
backend/tests/__init__.py
backend/requirements.txt
pyproject.toml
Makefile
docker-compose.yml
```

If you need more context, use search first and read only the minimal required file.

Implementation rules:

1. Use TDD.
2. First create a failing test.
3. Run the test and confirm failure.
4. Implement the minimum code required.
5. Run tests again and confirm pass.
6. Run lint and typecheck.
7. Validate Docker Compose config.
8. Update task status.
9. Update PROJECT_STATUS.md.
10. Stop.

Commands to use:

```bash
make test
make lint
make typecheck
docker compose config
```

If Docker daemon is unavailable, do not fail the task.
Instead:

- validate `docker compose config` if possible;
- note the limitation in `PROJECT_STATUS.md`;
- continue.

Expected endpoint:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "upcp-backend"
}
```

Do not add:

- database models;
- auth;
- frontend;
- MCP;
- LLM;
- Git integration;
- extra dependencies unless required for the task.

Token economy:

- keep final summary under 30 lines;
- do not output whole files unless necessary;
- do not paste long logs;
- use small diffs;
- stop if context becomes too large.

If blocked:

- write the blocker in `PROJECT_STATUS.md`;
- create a small clarification task if needed;
- stop.

If git repository exists, create a local commit:

```text
chore(repo): scaffold health endpoint [UPC-1]
```

Do not push.

Final output must contain:

```text
Summary
Files changed
Tests added
Commands run
Evidence
Next task
Blockers
```
'''

FILES["prompts/01-task-implementation-template.md"] = r'''
You are Qwen CLI working inside the UPCP repository.

Follow `AGENTS.md` strictly.

Current task:

```text
tasks/TASK-XXXX-short-name.md
```

Allowed context:

```text
AGENTS.md
PROJECT_STATUS.md
tasks/TASK-XXXX-short-name.md
related spec if referenced
only files required by the task
```

Rules:

1. Use Spec Flow.
2. Use DDD boundaries.
3. Use TDD.
4. Keep context minimal.
5. Do not modify unrelated files.
6. Do not add dependencies unless required.
7. Do not change public contracts unless task explicitly requires it.
8. Stop if task is ambiguous or too large.

Workflow:

```text
read task
write failing test
confirm failure
implement minimal code
confirm pass
run lint/typecheck/tests
update task status
update PROJECT_STATUS.md
stop
```

Final output:

```text
Summary
Files changed
Tests added
Commands run
Evidence
Next task
Blockers
```
'''

FILES["prompts/10-pro-audit-prompt.md"] = r'''
You are a Pro-level engineering auditor.

Audit the UPCP repository for production-grade quality.

Focus areas:

1. Spec Flow compliance.
2. DDD boundary compliance.
3. TDD compliance.
4. Test coverage gaps.
5. Security issues.
6. Secret handling.
7. Error handling.
8. Logging hygiene.
9. API contract stability.
10. Docker and local dev safety.
11. Token economy compliance.
12. File size and module complexity.

Do not rewrite the codebase.

Produce:

```text
Critical issues
High issues
Medium issues
Low issues
Recommended next tasks
```

Rules:

- Be concrete.
- Reference files.
- Do not invent issues.
- Prefer small reversible recommendations.
- Mark security and data-integrity issues as critical.
- Do not include secrets in the report.
'''

FILES[".env.example"] = r'''
# UPCP local environment

# External ports
UPCP_HTTP_PORT=38080
UPCP_POSTGRES_PORT=35432
UPCP_PROMETHEUS_PORT=39090
UPCP_GRAFANA_PORT=33000
UPCP_FRONTEND_DEV_PORT=35173

# Postgres
POSTGRES_USER=upcp
POSTGRES_PASSWORD=upcp_local_change_me
POSTGRES_DB=upcp

# Used by app container to reach DB internally
DATABASE_URL=postgresql+psycopg://upcp:upcp_local_change_me@db:5432/upcp

# App
UPCP_ENV=local
UPCP_LOG_LEVEL=INFO
UPCP_DEBUG=false

# Security placeholders
UPCP_SECRET_KEY=change_me_local_only
UPCP_SESSION_TTL_HOURS=24
UPCP_PAT_MAX_AGE_DAYS=365
UPCP_AGENT_TOKEN_MAX_AGE_DAYS=90

# LLM optional
UPCP_LLM_ENABLED=false
UPCP_LLM_DEFAULT_CLASS=light
UPCP_LLM_LIGHT_BASE_URL=http://localhost:8000/v1
UPCP_LLM_LIGHT_MODEL=MiMo-V2.5
UPCP_LLM_LIGHT_API_KEY_ENV=UPCP_LLM_LIGHT_API_KEY
UPCP_LLM_HEAVY_BASE_URL=
UPCP_LLM_HEAVY_MODEL=
UPCP_LLM_HEAVY_API_KEY_ENV=UPCP_LLM_HEAVY_API_KEY
UPCP_LLM_REDACT_SECRETS=true
UPCP_LLM_CACHE_ENABLED=true
UPCP_LLM_CACHE_TTL_SECONDS=3600

# Git sync
UPCP_GIT_SYNC_DEFAULT_MODE=polling
UPCP_GIT_SYNC_INTERVAL_SECONDS=300

# Retention defaults
UPCP_AUDIT_HOT_DAYS=365
UPCP_AUDIT_ARCHIVE_DAYS=1095
UPCP_REPORT_HOT_DAYS=180
UPCP_NOTIFICATION_READ_DAYS=30
UPCP_LLM_PAYLOAD_RETENTION_DAYS=14
UPCP_METRICS_RAW_DAYS=30

# Grafana optional
GRAFANA_ADMIN_PASSWORD=admin_change_me
'''

FILES["docker-compose.yml"] = r'''
name: upcp

services:
  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-upcp}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-upcp_local_change_me}
      POSTGRES_DB: ${POSTGRES_DB:-upcp}
    ports:
      - "127.0.0.1:${UPCP_POSTGRES_PORT:-35432}:5432"
    volumes:
      - upcp_pgdata:/var/lib/postgresql/data
    healthcheck:
      test:
        - CMD-SHELL
        - pg_isready -U ${POSTGRES_USER:-upcp} -d ${POSTGRES_DB:-upcp}
      interval: 5s
      timeout: 3s
      retries: 10

  app:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql+psycopg://upcp:upcp_local_change_me@db:5432/upcp}
      UPCP_ENV: ${UPCP_ENV:-local}
      UPCP_LOG_LEVEL: ${UPCP_LOG_LEVEL:-INFO}
      UPCP_DEBUG: ${UPCP_DEBUG:-false}
      UPCP_SECRET_KEY: ${UPCP_SECRET_KEY:-change_me_local_only}
    ports:
      - "127.0.0.1:${UPCP_HTTP_PORT:-38080}:8080"
    volumes:
      - ./backend/app:/app/app
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 10s

  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    profiles:
      - observability
    ports:
      - "127.0.0.1:${UPCP_PROMETHEUS_PORT:-39090}:9090"
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml:ro

  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    profiles:
      - observability
    ports:
      - "127.0.0.1:${UPCP_GRAFANA_PORT:-33000}:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin_change_me}
    volumes:
      - upcp_grafana:/var/lib/grafana

volumes:
  upcp_pgdata:
  upcp_grafana:
'''

FILES["Dockerfile"] = r'''
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
'''

FILES["backend/requirements.txt"] = r'''
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
pydantic>=2.8,<3.0
pydantic-settings>=2.4,<3.0
SQLAlchemy>=2.0,<3.0
alembic>=1.13,<2.0
psycopg[binary]>=3.2,<4.0
httpx>=0.27,<1.0
typer>=0.12,<1.0
python-multipart>=0.0.9
passlib[bcrypt]>=1.7,<2.0
PyJWT>=2.9,<3.0
prometheus-client>=0.20,<1.0

# dev/test
pytest>=8.3,<9.0
pytest-asyncio>=0.24,<1.0
ruff>=0.6,<1.0
mypy>=1.11,<2.0
'''

FILES["pyproject.toml"] = r'''
[tool.ruff]
line-length = 100
target-version = "py312"
exclude = [
  ".venv",
  "node_modules",
  ".git",
  "__pycache__"
]

[tool.ruff.lint]
select = [
  "E",
  "F",
  "I",
  "UP",
  "B",
  "SIM"
]
ignore = [
  "E501"
]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
exclude = [
  ".venv",
  "node_modules"
]

[tool.pytest.ini_options]
pythonpath = ["backend"]
testpaths = ["backend/tests"]
asyncio_mode = "auto"
'''

FILES[".gitignore"] = r'''
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.mypy_cache/
.pytest_cache/
.ruff_cache/

# Env
.env
.env.local
.env.*.local

# Docker
docker-compose.override.yml

# Node/frontend
node_modules/
dist/
build/
.vite/

# IDE
.idea/
.vscode/
*.iml

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Local data
data/
backups/
*.sqlite
*.sqlite3
'''

FILES["backend/app/__init__.py"] = "# UPCP backend package.\n"
FILES["backend/tests/__init__.py"] = "# UPCP backend tests package.\n"

FILES["observability/prometheus.yml"] = r'''
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: upcp-app
    metrics_path: /metrics
    static_configs:
      - targets:
          - app:8080
'''

MAKEFILE = """\
.PHONY: help install test lint typecheck format up down logs clean

help:
\t@echo 'Available commands:'
\t@echo '  make install    - create venv and install dependencies'
\t@echo '  make test       - run pytest'
\t@echo '  make lint       - run ruff'
\t@echo '  make typecheck  - run mypy'
\t@echo '  make format     - format code with ruff'
\t@echo '  make up         - docker compose up'
\t@echo '  make down       - docker compose down'
\t@echo '  make logs       - docker compose logs'

$(VENV)/bin/activate:
\tpython3 -m venv $(VENV)
\t$(PIP) install --upgrade pip
\t$(PIP) install -r backend/requirements.txt

install: $(VENV)/bin/activate

test: install
\t$(VENV)/bin/pytest backend/tests -q

lint: install
\t$(VENV)/bin/ruff check backend

typecheck: install
\t$(VENV)/bin/mypy backend/app

format: install
\t$(VENV)/bin/ruff format backend

up:
\tdocker compose up --build

down:
\tdocker compose down

logs:
\tdocker compose logs -f app db

clean:
\trm -rf .venv
\tfind . -type d -name __pycache__ -prune -exec rm -rf {} +
"""

FILES["Makefile"] = MAKEFILE


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap UPCP repository structure and agent docs."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target directory. Default: current directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print files that would be created.",
    )
    args = parser.parse_args()

    root = Path(args.target).expanduser()
    root.mkdir(parents=True, exist_ok=True)

    if root.exists() and root.is_file():
        print(f"ERROR: target path is a file: {root}", file=sys.stderr)
        return 1

    created = 0
    skipped = 0
    overwritten = 0

    for rel_path, content in FILES.items():
        file_path = root / rel_path
        content = content.lstrip("\n")
        if not content.endswith("\n"):
            content += "\n"

        if args.dry_run:
            print(f"would write: {file_path}")
            continue

        if file_path.exists() and not args.force:
            print(f"skip existing: {file_path}")
            skipped += 1
            continue

        file_path.parent.mkdir(parents=True, exist_ok=True)

        existed = file_path.exists()
        file_path.write_text(content, encoding="utf-8")

        if existed:
            print(f"overwrite: {file_path}")
            overwritten += 1
        else:
            print(f"create: {file_path}")
            created += 1

    if args.dry_run:
        return 0

    print()
    print("UPCP bootstrap complete.")
    print(f"Target directory: {root.resolve()}")
    print()
    print("Created:", created)
    print("Skipped:", skipped)
    print("Overwritten:", overwritten)
    print()
    print("Next steps:")
    print(f"  cd {root}")
    print("  cp .env.example .env")
    print("  make install")
    print("  make test")
    print()
    print("Then start Qwen CLI and paste:")
    print("  prompts/00-initial-qwen-prompt.md")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
