# TASK-0138 — Pre-existing e2e debt: fix ~102 failing Playwright tests

**Milestone:** test quality (follow-up from TASK-0128 evidence)
**Points:** 8
**Spec:** mini-spec (this file)
**Status:** DONE (closed 2026-10-17)

## Context

Full `frontend/e2e` suite: **102 failed / 56 passed** — identical failure
counts on clean baseline (develop HEAD), so all rot is pre-existing, not a
regression. Root causes identified from baseline log:

1. **`comprehensive-ui.spec.ts` (23 failures, 21 = ECONNREFUSED 127.0.0.1:3072)**
   — spec tests against a LIVE backend (`UPCP_PORT_FRONTEND` default 3072);
   dev stack not running during CI-style runs.
2. **`mockWorkflowApis` group — 48 failures**: `agent-workflow` (16),
   `evidence-review` (13), `delivery` (13), `dashboard` (6) — shared fixtures
   (`e2e/fixtures/helpers.ts`, `mock-data.ts`) drifted vs current UI
   (dashboard redesign SPEC-0025, universal filtering SPEC-0026, sprint 5-7
   UX changes): selectors/text/route shapes changed.
3. **Independent specs — 31 failures**: `navigation` (7), `command-palette`
   (7), `projects` (5), `keyboard-shortcuts` (4), `components` (3), `theme`
   (2), `error-states` (2), `integration` (1) — UI rot (labels, structure),
   no fixture usage.

## Decomposition (parallel, disjoint file ownership)

- Agent 1: `comprehensive-ui.spec.ts` + live dev stack (started via
  `docker compose --env-file .env.dev up -d`).
- Agent 2: mockWorkflowApis group (4 spec files) + **owns**
  `e2e/fixtures/*`.
- Agent 3: independent specs (8 files) — spec files ONLY, must not edit
  `e2e/fixtures/*` (report needed fixture changes instead).

## AC

- [x] Full `npx playwright test` → 0 failed — **153 passed / 0 failed, EXIT=0** (5.4m)
- [x] No fixtures regressions: mockWorkflowApis group still green after
      Agent 3's changes — verified: dashboard-redesign + accessibility
      30/30 green after fixture changes; Agent 3's 8 specs 40/40 after
      fixture owner's `gotoPage` fixes (29/31 of its baseline failures were
      cured by those fixture fixes)
- [x] `npm run lint` + `npx tsc --noEmit` clean (0 errors, 3 pre-existing
      warnings outside changed files); frontend vitest suite still
      **429/429** (no src changes — `git status frontend/src` empty)
- [x] Tests remain deterministic — mock-based except comprehensive-ui
      against local dev stack (per-run unique data suffixes, no DB resets)

## Evidence

- Final full run: `npx playwright test --reporter=list` → **153 passed,
  0 failed, EXIT=0** (was 102 failed / 56 passed at baseline).
- Per-agent closeout:
  - **comprehensive-ui (23 → 0)**: root causes — `waitForLoadState
    ('networkidle')` never settles (SSE keeps connection open; 21 sites →
    `'load'`), backend rate limiter 429 (retry helpers + windows), global
    non-idempotent create data → per-run unique suffixes, comma-list
    selectors (`text=A, text=B`) never match in Playwright → regex,
    inverted console-error filter (caught own bug mid-run).
  - **mockWorkflowApis group (48 → 0)**: `mockAllApis` registered its
    catch-all `**/api/**` LAST — Playwright matches LIFO, so it shadowed
    every specific mock AND intercepted frontend module URLs (blank page,
    all clicks timed out); catch-all now first + scoped to `/api/v1/`.
    Plus stale route shapes (KPI fields, attention fields, board tasks,
    notifications), `MOCK_CLAIMS.state 'active' → 'claimed'`, stale
    selectors (KPI labels, dedicated tabs), `gotoPage({workflow,
    beforeGoto})` for pre-navigation mock registration (30s staleTime).
    **5 tests deleted with justification**: verdict accept/reject controls
    no longer exist anywhere in the UI (feature removed) + 1 vacuous stub.
  - **independent specs (31 → 0)**: 29 cured by fixture owner's
    `gotoPage` fix; 2 real fixes — race (instant `count()` before render)
    and stale CSS selector; assertions strengthened (accessible names,
    explicit waits), 0 fixme/blocked.
- **Last failure found & fixed post-merge-run: `auth.spec.ts:59`** —
  with the dev stack UP, background `notifications/unread-count` 401 →
  `client.ts:83-90` `window.location.href='/login'` yanks `/setup`
  mid-test (with stack down the request fails as network error → no 401 →
  no redirect; that's why it passed at baseline). Fixed test-side: mock
  notification endpoints + assert setup heading. Also found the sibling
  "toggle" test passed **vacuously on /login** (login has the same
  Password+toggle elements) — now guarded by heading assertion. auth 6/6.
- Product-level finding (NOT fixed here, out of scope): public pages
  (`/setup`) get hard-redirected by background notification polling's 401
  — logged as follow-up in PROJECT_STATUS.
