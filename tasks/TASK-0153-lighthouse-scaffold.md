# TASK-0153 — Lighthouse frontend-perf scaffold (SPEC-0024 requirement, TASK-0140 finding)

**Spec:** SPEC-0024 §Load testing — "Locust (Python), all endpoints + **frontend (Lighthouse)**"; TASK-0140 follow-up: "Lighthouse frontend perf (spec mentions it; not in README/scaffold)"
**Milestone:** Этап 1 perf-расследования (last item)
**Points:** 3
**Status:** DONE (closed 2026-10-25)

## Investigation (2026-10-25)

- Zero lighthouse/lhci artifacts in the repo (only the finding
  mentions) — the SPEC's frontend half of load testing was absent.
- Toolchain on host: node v22.23.2, npx 12, `/usr/bin/google-chrome`
  156 + puppeteer chrome-headless-shell — no installs required.
- `quality:gate` CI job boots the test stack in-network (nginx on
  `http://nginx`, LOCUST_HOST `app:8080`) but its image is
  python-slim — no Node — and runner-hardware perf budgets need their
  own calibration (gate-stability note: the job already needs bounded
  retries for external fetches).

## Objective

Runnable local scaffold: LHCI config with a **measured** performance
budget, `make lighthouse` entry point, README contract, artifacts
gitignored — closing the SPEC gap without package.json/lock churn.

## Acceptance Criteria (verified 2026-10-25)

- [x] **Red-of-absence:** `lhci collect --config=…/lighthouserc.json`
      before the scaffold → `ENOENT`, exit 1
- [x] Measured baseline on the test stack (3 runs): performance
      **0.87 / 0.88 / 0.88 → median 0.88**; budget calibrated to
      **0.8** (median − margin)
- [x] Full `autorun` GREEN (`exit 0`): healthcheck ✓, 3 runs on
      `http://localhost:3071/`, assertions passed, reports +
      `assertion-results.json` dumped to `lighthouse/.lighthouseci/`
- [x] Deliverables: `tests/performance/lighthouse/lighthouserc.json`,
      `make lighthouse` (help entry + `.PHONY` + dry-run verified),
      README section (Quick Start + Lighthouse section + Files tree),
      gitignore rule `lighthouse/.lighthouseci/` (check-ignore verified)
- [x] Stack torn down (`compose down`, env lifecycle)
- [x] PROJECT_STATUS updated

## Evidence

- Red: `ENOENT: …/tests/performance/lighthouse/lighthouserc.json`, exit 1
- Collect: `Running Lighthouse 3 time(s)… Done` + scores above
- Autorun: `Healthcheck passed! … Done running autorun`, AUTORUN=0;
  artifacts in `tests/performance/lighthouse/.lighthouseci/`
  (assertion-results.json + 3× html/json), ignored by git
- `make help` lists `make lighthouse`; `make -n` shows the recipe

## Deviations / notes (recorded per §7)

1. **CI wiring deferred** (follow-up): `quality:gate` runs on
   python-slim (no Node) and budgets must be calibrated on runner
   hardware before a hard-gate; decision + reasons recorded in the
   README Lighthouse section and here. The local scaffold satisfies the
   SPEC requirement (suite runnable + documented + budgeted).
2. **No package.json/lock changes**: LHCI is fetched via pinned
   `npx @lhci/cli@0.14.0` each run — avoids the frontend lock-regen
   risk entirely (memory: npm-lock EACCES/CI npm ci drift).
3. Opportunistic doc fix: `tests/performance/README.md` Grafana access
   line claimed `admin/admin_test` — corrected to the TASK-0152
   init-once truth (stale claim discovered while editing the same file).

## Files

| File | Action |
|------|--------|
| `tests/performance/lighthouse/lighthouserc.json` | CREATE — collect/assert/upload (budget 0.8) |
| `Makefile` | MODIFY — `lighthouse` target + help + .PHONY |
| `tests/performance/README.md` | MODIFY — Quick Start, Lighthouse section, Files tree, Grafana password line |
| `tests/performance/.gitignore` | MODIFY — `lighthouse/.lighthouseci/` |
