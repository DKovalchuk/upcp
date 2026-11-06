# TASK-0143 — SPEC-0024 Phase 5: Integration — quality gate in CI, aggregate reporter, docs

**Milestone:** SPEC-0024 (Test Environment) Phase 5
**Points:** 8
**Spec:** `specs/SPEC-0024-test-environment.md` (Nightly + on-merge
triggers; reports Markdown + JSON; regression comparison without strict
thresholds; results versioning). Grafana dashboard ingestion explicitly
deferred (recorded in TASK-0142 deviations).
**Status:** DONE (closed 2026-10-18 — all AC verified; phase-B flip
landed in this branch: `allow_failure: false` after 2 green develop gate
runs (jobs 3330/3371, pipelines 460/463) + 1 green schedule run (job
3345, pipeline 461 full); the flip MR's own pipeline is the first
hard-gate validation)

## Mini-spec (design decisions — agreed with Dmitry 2026-10-18)

### Tiering (what runs where)

| Tier | Trigger | Content |
|------|---------|---------|
| MR | merge_request_event | unchanged (lint/typecheck/unit/vitest/SAST) — no heavy stacks |
| develop-merge | push develop | **quality gate**: e2e (root + frontend), chaos quick, security baseline, perf smoke — ephemeral stack; blocks deploy once flipped to hard gate (stage order lint→test→quality→build→deploy) |
| Nightly | pipeline schedule (~03:00 Europe/Moscow, develop) | **full**: chaos full, security full (ZAP+Kali), perf load (allow_failure forever), e2e |
| On demand | run the schedule (`POST .../pipeline_schedules/1/play` or UI ▶), or run locally (docs §6) | no dedicated manual job (deviation below) |

### Failure policy (two phases)

Phase A: `quality:gate` with `allow_failure: true` — first observations in
CI. Phase B (follow-up commit within this task): after **≥2 green
develop + ≥1 green schedule** gate runs observed → flip to hard gate.
`perf load` never gates (honest red SLO, TASK-0140); perf RC counts only
on the `quick` profile.

### Environments (tables in docs/ops/environments.md)

dev (local `upcp` / CI `upcp-dev`, ports 3073/38083/35435/36384, own
data) · test (local `upcp-test` + mandatory `--env-file .env.test` /
**CI ephemeral `upcp-test-ci`** via `.env.ci`) · stage (`upcp-stage`,
sole owner = deploy:stage) · **prod — documented future model only**.
Environment urls: dev → 3073, stage → 3070 (were stale 3080).

### Mechanics (docs/ops/ci-quality-gates.md §3)

One quality job per tier (setup+suites+aggregate+teardown in one job —
fresh checkout per job would break cross-job bind mounts). Suites run
**inside the gate network** (job joins via `docker network connect` with
`.Config.Hostname`-resolved container id — runner hostname ≠ daemon
name). Env contract: `SECURITY/CHAOS_BASE_URL`+`LOCUST_HOST` →
`http://app:8080`; root e2e → `http://nginx` + `E2E_API_BASE`;
frontend e2e → own vite + `VITE_API_URL`; `E2E_ADMIN_PASSWORD`
(dev default `admin123`, gate `TestAdmin123!`); authz DB via
`SECURITY_DB_HOST=db`/`PORT=5432` (in-network). e2e in the playwright
container (uid 1000, `HOME=/tmp`). Runner-level prerequisite (approved
by Dmitry): config.toml `volumes += "/builds:/builds"` so host daemon
sees job-workspace bind sources (backup `config.toml.bak-20261018`).

## AC

- [x] Hermetic CI stack support (`.env.ci`, env-driven data dirs, `e2e`
      service) — proven by full local rehearsal (build → up → health →
      seed → suites → aggregate → down; other stacks untouched)
- [x] `quality:gate` job (stack → seed → suites → report → teardown
      always, phase-A `allow_failure: true`) — rehearsed locally with
      exact CI invocations; CI Lint valid; **verified in real CI**:
      job 3330 (develop, quick) **success 462.5s**, job 3345 (schedule,
      full) **success 797.8s**
- [x] Nightly schedule: `workflow.rules` += schedule; schedule **id 1**
      created via API (develop, 03:00 Europe/Moscow,
      `QUALITY_PROFILE=full`); first full run observed green (pipeline
      461 / gate 3345); play endpoint documented (docs §7)
- [x] Aggregate reporter with unit tests (red→green, 10 tests) incl.
      regression-vs-baseline section; runs as gate step 1 + step 5
- [x] Deploy topology split: deploy:dev own project/ports/group/url,
      deploy:stage sole owner of upcp-stage; urls corrected; validated
      via CI Lint + config simulations (dev → `upcp-dev`:38083; clean-env
      stage → `upcp-stage` 38081/35433/3070/36382 unchanged)
- [x] e2e baseURL + credential parameterization — dev 22/22 + 153/153;
      gate container 22/22 + 153/153 (verified in job 3330)
- [x] Two-phase flip to hard gate — **2/2 green develop observed (gate
      3330 pipeline 460 + gate 3371 pipeline 463) + 1/1 green schedule
      (gate 3345, pipeline 461 full)**; flip landed in this branch:
      `allow_failure: false` + bounded before_script install retry (the
      p463 download.docker.com flap killed a healthy gate pre-start);
      perf load stays non-gating
- [x] Docs written + INDEX updated (`docs/ops/environments.md`,
      `docs/ops/ci-quality-gates.md`) — §6/§7 kept in sync through the
      rounds (env-source gotcha, collision warning, schedule exists)
- [x] Spec exit criteria end-to-end (CI/CD triggers tests on schedule
      and events): green develop gate ✅ (jobs 3330, 3371) + green
      schedule gate ✅ (job 3345, full profile via schedule id 1) +
      report artifacts uploaded by every gate run (30-day CI artifacts)

## Evidence

**Local rehearsal (ephemeral `upcp-test-ci`, exact CI invocations) —
all green:** reporter unit 10 passed, aggregate RC=0, health 200, seed
RC=0, root e2e 22 RC=0, frontend e2e 153 RC=0, chaos quick 3/3 RC=0,
security baseline RC=0 (authz 52/55 + 3 xfail, fuzz 55/55, zap 2/2),
perf smoke RC=0 SLO 363/363, teardown clean, other stacks untouched.

**CI observations (red → green across 4 fix rounds, MR !71 → !75):**

| Pipeline | Gate | Result | What it taught |
|---|---|---|---|
| 449 (first ever) | 3201 | red (allow_failure) | workspace invisible to host daemon → nginx bind fail |
| 449 retry | 3206 | red | runner hostname ≠ container name → connect fail; runner fix (approved): `volumes += /builds:/builds`, garbage wiped, restarted |
| 451/452 | 3221/3236 | red `e2e_fe=1 chaos=1` | empty-state e2e strict-mode violations; chaos `health_url` hardcoded :38082 (masked locally by local test stack); 4MB log cap cut full-run verdict |
| 454 | gate skipped | backend:test red | wall-clock flake `velocity 1.12s < 1.0` under `-n auto` |
| 455 (schedule) | 3277 | red `chaos=1` | chaos integrity/traffic still on :38082 (`api_url`/`data_url`) |
| 457/458 | 3296/3311 | red `security=1` / early death | psycopg missing → RBAC skips restored → exposed agent create→token 404 race; 3311 = local stack held :35436 (§6 collision) |
| **460 (develop)** | **3330** | **SUCCESS 462.5s** | **develop observation ✅ #1** |
| **461 (schedule, full)** | **3345** | **SUCCESS 797.8s** | **schedule observation ✅ #1** (chaos full, security full, perf load 2143/2145 SLO, e2e 22+153) |

**Wiring/product bugs found & fixed (each reproduced first):**
1. gate would use dev compose file → `COMPOSE_FILE` job variable
2. authz wrong-DB (localhost vs in-network) → `SECURITY_DB_HOST/PORT`
   + `SECURITY_DB_PORT` local — **and psycopg missing from requirements**
   → skips restored (5→1)
3. `nginx.test.conf` no `/auth` location → added
4. e2e `HOME=/home/pwuser` unwritable (pwuser uid 1001 ≠ 1000) → `/tmp`
5. e2e `admin123` (dev) vs `TestAdmin123!` (test) → `E2E_ADMIN_PASSWORD`
6. root-owned `frontend/node_modules` rot → wiped, rebuilt uid-1000
7. runner hostname ≠ daemon name → `.Config.Hostname` resolve loop
8. chaos `health_url`/`api_url`/`data_url` hardcoded :38082 → derived
   from `CHAOS_BASE_URL` (identity proofs pre/post; quick 3/3)
9. `velocity`/`portfolio` `<1.0s` CI flake → `_BUDGET_S` (1s local / 2.5s CI)
10. agent `create/token/revoke` flush-only → commit-before-respond (TDD
    3-fail → 5-pass; same class as TASK-0140) — last red-gate root cause
11. env pollution (OS env > `--env-file`) + `upcp-test-ci` local/CI
    teardown collision → docs §6 warnings + memory

**Validation:** CI Lint valid (every yaml revision) · `compose config`
OK · deploy split simulations OK · `ruff check tests/` clean · A-matrix
16 passed · full backend suite **975 passed** exit 0 · frontend oxlint
0 errors.

**History (atomic commits per concern):** MR **!71** main build (7
commits: `9f7e053` `0f5e54f` `ef16f19` `d4c6157` `394274c` `86cee9c`
`7aaf5f6`) · **!72** runner-connect+chown (`5753bed`) · **!73** e2e
empty-state + chaos health_url + in-network DB + log-cap (`f3f1192`
`3001b25` `05bfc46`) · **!74** chaos all-URLs + psycopg + budgets +
docs (`e89c810` `b94c7e7` `c70ecb0` `54917d0`) · **!75** agent commit
(`f8cb581`).

## Deviations

- **Grafana**: quality-report JSON is the integration point; no new
  dashboard (deferred per TASK-0142).
- **Manual tier**: no dedicated manual job — schedule play / local runs
  (docs §1).
- **Results versioning**: raw JSON/CSV = local + CI artifacts (30d);
  markdown reports + perf baselines tracked in git — deviates from the
  spec's "JSON results in repo" (docs §4).
- **Docs §7** refreshed in !73 (was written pre-schedule) — resolved.

## Follow-ups

- Resolved: all observation prerequisites met (2 develop + 1 schedule
  green) and the flip landed in this branch. **Post-merge watch:** the
  flip MR's own pipeline is the first run of the hard gate — if it goes
  red the gate is doing its job (investigate the suite, not the flag).
- From TASK-0142/0140 findings queues remain in PROJECT_STATUS (RBAC
  spec decisions, dashboard/stats perf, throughput) — unrelated to this
  task.
