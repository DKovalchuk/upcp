# TASK-0020 Context Pack Generator

Status: done
Owner: backend-developer
Milestone: M4
Depends on: TASK-0019
Related tasks: TASK-0021

## Problem

AI agents need structured context packs to understand projects and tasks. No generator exists.

## Goal

Create context pack generator that produces markdown context packs for AI agents. Include project info, tasks, features, git links.

## Requirements

1. Create `backend/app/mcp/context_pack.py` with `ContextPackGenerator`.
2. Generate markdown with sections: project, tasks, features, git links.
3. Include project metadata: name, slug, status, description.
4. Include tasks: title, status, priority, assignee.
5. Include features: title, status, components.
6. Include git links: branches, commits, PRs.
7. Output: structured markdown.
8. Add tests for generator.
9. Integrate with MCP resource endpoint.

## Acceptance Criteria

- `ContextPackGenerator` creates markdown for project.
- Sections: project, tasks, features, git links.
- Output is valid markdown.
- Tests pass.
- Lint and typecheck pass.

## DoD

- All acceptance criteria satisfied.
- `make test`, `make lint`, `make typecheck` pass.
- Status updated.