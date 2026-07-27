# Changelog

All notable changes to UPCP will be documented in this file.

## [Unreleased]

### Added
- M0: Repository scaffold, health endpoint, config, logging, errors
- M0: Database base, Alembic migrations
- M0: Audit event append-only model
- M1: Project CRUD with pagination, filters, sorting
- M1: RBAC placeholder (User, Role, Permission)
- M1: Shared pagination, IDs, response schemas
- M2: Component and Module CRUD (structure context)
- M2: Feature, Task, Subtask CRUD (delivery context)
- M2: Acceptance criteria, DoD items, quality gate
- M3: Git read integration (local + GitHub adapters)
- M4: MCP server, tools, context pack generator
- M4: Typer CLI with project/task/status commands
- M5: React frontend with Vite, Tailwind, shadcn/ui
- M6: Report generation, markdown export, LLM summary
- M6: LLM redaction layer for secrets
- Phase 1 audit fixes: DRY helpers, DDD boundaries, FK indexes

### Fixed
- Added missing FK indexes (migration 0008)
- Moved RBAC models to app/auth/ context
- Fixed quality→delivery boundary inversion

## [0.1.0] - 2026-07-24

### Added
- Initial project setup
