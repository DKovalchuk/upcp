# TASK-0022 React + Vite + Tailwind Scaffold

Spec: SPEC-0006 (Frontend spec) — backlog
Status: done
Priority: 10
Model: routine
Milestone: M5

## Goal

Create the React frontend scaffold with Vite, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, and TanStack Router. Configure API proxy to backend (port 38080). Add frontend as optional service in docker-compose.

## Non-goals

- No UI components beyond scaffold.
- No data fetching beyond sample.
- No routing beyond root.
- No tests (will be added in subsequent tasks).

## Files likely involved

```text
frontend/
frontend/package.json
frontend/vite.config.ts
frontend/tsconfig.json
frontend/tailwind.config.js
frontend/postcss.config.js
frontend/src/main.tsx
frontend/src/App.tsx
frontend/src/index.css
frontend/src/lib/api.ts
frontend/src/components/ui/ (shadcn components)
frontend/.gitignore
docker-compose.yml
```

## TDD Steps

1. Initialize Vite project.
2. Install dependencies.
3. Configure Tailwind.
4. Add shadcn/ui components (Table, Card, Button).
5. Configure API proxy.
6. Add frontend service to docker-compose.
7. Verify build passes.

## Acceptance Criteria

- `frontend/` directory exists with Vite + React + TypeScript.
- Tailwind CSS configured with custom theme (6-color palette).
- shadcn/ui installed and configured.
- TanStack Query and TanStack Router installed.
- API proxy configured to `http://localhost:38080`.
- `npm run build` succeeds.
- `npm run dev` starts on port 35173.
- Frontend added as optional service in docker-compose.
- `.gitignore` includes `node_modules`, `dist`.
- No TypeScript errors.

## Commands

```bash
cd frontend
npm run build
npm run dev
```

## DoD

- scaffold created;
- dependencies installed;
- build passes;
- docker-compose updated;
- gitignore updated.