# PROJECT_STATUS

Updated: 2026-07-24
Milestone: M5
Current Task: TASK-0024 (done)
Next Task: M5 — TASK-0025
Blockers: none

## Last Result

M4 completed: MCP and CLI.

- `backend/app/mcp/`: MCP server scaffold with JSON-RPC endpoint.
- MCP tools: project_list, project_get, task_list, task_get, feature_list, feature_get.
- Context pack generator: markdown context packs for AI agents.
- `backend/cli.py`: Typer CLI with project, task, status commands.
- Tests: 22 new tests for MCP and CLI.
- Coverage: 82%.
- Lint: all checks passed.
- Typecheck: MCP/CLI files pass (some pre-existing errors in other files).

TASK-0022 and TASK-0023 completed.

- `frontend/` directory created with React + Vite + TypeScript scaffold.
- Tailwind CSS configured with 6-color palette.
- shadcn/ui components (Table, Card, Button) installed.
- TanStack Query and TanStack Router configured.
- API proxy to backend (port 38080) configured.
- Frontend added as optional service in docker-compose.
- Portfolio view (project list) implemented at route `/`.
- Projects fetched from `/api/v1/projects` and displayed in responsive table.
- Loading, error, and empty states handled.
- `npm run build` passes with no TypeScript errors.

M5 in progress: Frontend UI/UX.

- SPEC-0012 created: Frontend UI/UX Architecture.
- TASK-0024: App Shell + Sidebar + TopBar (done).
- TASK-0025: Design System Components (pending).
- TASK-0026: Types + API Client + Hooks (pending).
- AGENTS.md updated: Git Workflow section (feature branches, commit format).
- App Shell implemented with Sidebar, TopBar, BreadcrumbBar.
- Responsive behavior: mobile (< 768px) sidebar hidden, tablet (768-1023px) collapsed, desktop (>= 1024px) expanded.
- shadcn/ui components installed: sidebar, separator, tooltip, avatar, dropdown-menu, skeleton, badge, input, dialog, select, sonner.

## Important Notes

- Use non-standard Docker ports.
- Use TDD.
- Keep context small.
- Read `AGENTS.md` before any task.
- All work via feature branches → merge to `develop`.
