# UPCP Work Plan

Created: 2026-07-24
Status: active
Owner: Dmitry

## Overview

7 milestones, ~40 tasks, modular monolith (Python/FastAPI + React).
All work via feature branches → `develop`. TDD mandatory.

---

## M0 — Repository and Health (in progress)

Foundation: scaffold, config, DB, audit.

| # | Task | Status | Model | Depends on |
|---|------|--------|-------|------------|
| 1 | TASK-0001 scaffold health endpoint | done | routine | — |
| 2 | TASK-0002 config, logging, error foundation | ready | routine | 1 |
| 3 | TASK-0003 database base + Alembic migrations | ready | routine | 2 |
| 4 | TASK-0004 audit event append-only model | ready | routine | 3 |

Exit criteria: `make test`, `make lint`, `make typecheck` pass. App starts in Docker. Health + audit log work.

---

## M1 — Core Project Model

Project CRUD, API schemas, pagination, error taxonomy.

| # | Task | Status | Model | Depends on |
|---|------|--------|-------|------------|
| 5 | SPEC-0002 Project CRUD spec | backlog | routine | 4 |
| 6 | TASK-0005 shared: pagination, IDs, error responses | backlog | routine | 4 |
| 7 | TASK-0006 project model + CRUD API | backlog | routine | 5, 6 |
| 8 | TASK-0007 project list + filters + sorting | backlog | routine | 7 |
| 9 | TASK-0008 RBAC placeholder (user, role, permission models) | backlog | pro | 7 |

Exit criteria: full CRUD on `/api/v1/projects`. Pagination works. Audit events fire on create/update/delete.

---

## M2 — Structure and Delivery

Components, modules, features, tasks, subtasks, quality gates.

| # | Task | Status | Model | Depends on |
|---|------|--------|-------|------------|
| 10 | SPEC-0003 Structure + Delivery spec | backlog | routine | 7 |
| 11 | TASK-0009 component + module CRUD | backlog | routine | 10 |
| 12 | TASK-0010 feature + task + subtask CRUD | backlog | routine | 11 |
| 13 | TASK-0011 acceptance criteria + DoD items | backlog | routine | 12 |
| 14 | TASK-0012 quality gate: task done only if DoD passes | backlog | routine | 13 |

Exit criteria: full hierarchy Project → Component → Module. Full delivery chain Feature → Task → Subtask. Quality gate blocks task completion.

---

## M3 — Git Read Integration

Read-only Git adapters for local, GitHub, GitLab.

| # | Task | Status | Model | Depends on |
|---|------|--------|-------|------------|
| 15 | SPEC-0004 Git read integration spec | backlog | pro | 12 |
| 16 | TASK-0013 git provider config model | backlog | routine | 15 |
| 17 | TASK-0014 local Git read adapter | backlog | routine | 16 |
| 18 | TASK-0015 GitHub read adapter (REST API) | backlog | routine | 16 |
| 19 | TASK-0016 GitLab read adapter (REST API) | backlog | routine | 16 |
| 20 | TASK-0017 branch/commit/PR → task linking | backlog | routine | 17–19 |

Exit criteria: UPCP reads branches/commits/PRs from configured repos. Links appear on tasks. No writes to project repos.

---

## M4 — MCP and CLI

Agent interface: MCP tools, context packs, Typer CLI.

| # | Task | Status | Model | Depends on |
|---|------|--------|-------|------------|
| 21 | SPEC-0005 MCP + CLI spec | backlog | pro | 12 |
| 22 | TASK-0018 MCP server scaffold | backlog | routine | 21 |
| 23 | TASK-0019 MCP tools: project, task, feature | backlog | routine | 22 |
| 24 | TASK-0020 context pack generator | backlog | routine | 23 |
| 25 | TASK-0021 Typer CLI (project, task, status) | backlog | routine | 23 |

Exit criteria: AI agents can query projects/tasks via MCP. CLI works from terminal. Context packs generate agent-ready markdown.

---

## M5 — Rich UI

React frontend: portfolio, dashboard, task board, quality view.

| # | Task | Status | Model | Depends on |
|---|------|--------|-------|------------|
| 26 | SPEC-0006 Frontend spec | backlog | routine | 12 |
| 27 | TASK-0022 React + Vite + Tailwind scaffold | done | routine | 26 |
| 28 | TASK-0023 portfolio view (project list) | done | routine | 27 |
| 29 | TASK-0024 project dashboard | backlog | routine | 28 |
| 30 | TASK-0025 task board (kanban) | backlog | routine | 29 |
| 31 | TASK-0026 task deep dive (detail view) | backlog | routine | 30 |
| 32 | TASK-0027 quality view (DoD, acceptance) | backlog | routine | 31 |

Exit criteria: full UI navigable. All CRUD operations work from browser. Responsive layout.

---

## M6 — Reports and Optional LLM

Reporting, markdown export, optional LLM summary.

| # | Task | Status | Model | Depends on |
|---|------|--------|-------|------------|
| 33 | SPEC-0007 Reports + LLM spec | backlog | routine | 12 |
| 34 | TASK-0028 daily report generator | backlog | routine | 33 |
| 35 | TASK-0029 markdown export | backlog | routine | 34 |
| 36 | TASK-0030 optional LLM summary (light model) | backlog | pro | 34 |
| 37 | TASK-0031 LLM redaction layer | backlog | pro | 36 |

Exit criteria: daily reports generate on schedule. Markdown export works. LLM summary is opt-in, secrets are redacted.

---

## Critical path

```text
M0: 1 → 2 → 3 → 4
M1: 4 → 5 → 6 → 7 → 8
M2: 7 → 10 → 11 → 12 → 13 → 14
M3: 12 → 15 → 16 → 17/18/19 (parallel) → 20
M4: 12 → 21 → 22 → 23 → 24/25 (parallel)
M5: 12 → 26 → 27 → 28 → 29 → 30 → 31 → 32
M6: 12 → 33 → 34 → 35, 34 → 36 → 37
```

## Parallelism opportunities

- M3 adapters (17, 18, 19) can run in parallel after 16.
- M4 CLI (25) and context packs (24) can run in parallel after 23.
- M5 and M6 can start in parallel once M2 is done.
- M3, M4, M5, M6 are largely independent after M2.

## Estimated effort

| Milestone | Tasks | Est. sessions |
|-----------|------:|--------------:|
| M0 | 4 | 2–3 |
| M1 | 5 | 3–4 |
| M2 | 5 | 4–5 |
| M3 | 6 | 3–4 |
| M4 | 5 | 3–4 |
| M5 | 7 | 5–6 |
| M6 | 5 | 3–4 |
| **Total** | **37** | **23–30** |

## Model allocation

- **Routine** (MiMo/DeepSeek): ~80% of tasks — CRUD, tests, docs, scaffolding.
- **Pro**: ~20% — specs, RBAC, Git adapters, LLM redaction, security review.

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM API instability | M6 blocked | LLM is optional, not on critical path |
| Git adapter complexity | M3 delayed | Start with local Git, add providers incrementally |
| Frontend scope creep | M5 delayed | Strict spec, shadcn/ui components, no custom design system |
| DB migration conflicts | Any milestone | One migration per task, Alembic linear history |
