# TASK-0140 — SPEC-0024 Phase 2: Performance — run suite, analyzer, SLI/SLO, evidence

**Milestone:** SPEC-0024 (Test Environment) Phase 2
**Points:** 8
**Spec:** `specs/SPEC-0024-test-environment.md` (milestones + exit criteria)
**Status:** DONE (closed 2026-10-18)

## Context

Scaffolding exists (committed in MR !56) but has **never been executed** —
no evidence, `locust` not installed anywhere, no perf requirements file.
`docs/planning/TEST_ENVIRONMENT_SPEC.md` referenced by the spec **does not
exist** (never in git) — AC derived from spec milestones/exit criteria +
`tests/performance/README.md`.

## AC

- [x] Test stack (`docker-compose.test.yml`) runs CURRENT code: app
      image rebuilt, healthy, migrations applied to test DB (0017→0023 —
      idempotent fix from TASK-0137), seeder clean-slate + seed (x1)
- [x] Performance tooling runnable: locust installed (2.46.7 in .venv),
      documented dependency path (`tests/performance/requirements.txt` added)
- [x] `runner.py --profile smoke` runs green end-to-end — **2 consecutive
      runs: EXIT=0, 0 request errors, SLO 375/375 and 378/378 met**; all
      script bugs found along the way fixed (list in Evidence)
- [x] `runner.py --profile load --report` produces markdown report with
      analyzer output incl. SLI/SLO evaluation vs `config/sli_slo.yaml` —
      `reports/load_20261018_002751.md` (1521 req, 119 failed = 7.82%,
      5.1 req/s), **SLO: 1114/1491 met** (honest failing verdict = finding)
- [x] Baseline saved (`--save-baseline`) into `tests/performance/results/`
      — `baseline.json` + `trend_history.json` (both tracked per .gitignore)
- [x] Grafana test dashboards provisioned & Prometheus scraping test app
      `/metrics` (verified via API, not UI screenshot)
- [x] Evidence: actual run outputs (RPS, p95, fail%, SLO verdicts), report
      file paths, findings list — see Evidence below

## Out of scope

- Phase 3 (chaos) — TASK-0141; Phase 4 (security) — TASK-0142;
  Phase 5 (integration/CI) — TASK-0143.
- Lighthouse frontend perf (spec mentions it; not in README/scaffold —
  flag as follow-up if absent).

## Evidence

**Runs:** smoke ×2 green (EXIT=0, 0 errors, SLO **375/375** and
**378/378**) · load → report `tests/performance/reports/load_20261018_002751.md`
+ **SLO 1114/1491 met** + `results/baseline.json` saved (locust exit 1
reflects the 119 timeouts below; analysis now runs on failed runs too) ·
prometheus API: `upcp-app up http://app:8080/metrics` (+ upcp-otel, self) ·
grafana API (admin:admin_change_me): 4 dashboards in "UPCP Test
Environment" (Overview/Performance/Resources/Chaos) · backend suite
**962 passed** (pool TDD red2→green13), ruff+mypy clean.

**Findings (the gate's output):**
1. **`GET /dashboard/stats` degrades with data volume** — standalone
   1.06–1.33s at 394 projects; under 50-user load it accounts for 117/119
   timeouts, aggregate p95+ pinned at the 60s client ceiling → follow-up
   perf task (per-project aggregation is the prime suspect).
2. **Throughput collapse at 50 users** — 5.1 req/s, p50 1.1s, p90 34s;
   suspects: sync-endpoint threadpool saturation (anyio default 40
   workers) and finding #1 → follow-up investigation.
3. First honest SLO verdict: smoke all-pass, load fails latency (1114/1491).

**Scaffold bugs fixed (first-ever execution of this suite):**
runner `--host` docker-only default (→ localhost:38082); health-check
`sys.path` import; analysis-gate `exit_code == 0` dropped reports exactly
when runs failed; `save_baseline` bool-shadowing (`bool not callable`);
seeder: `tests/` absent from image (bind-mount), 600-file perms vs
non-root `upcp` uid, passlib 1.7.4 × bcrypt 5 crash → pyca bcrypt +
requirements `passlib[bcrypt]` → `bcrypt>=4.0,<6`, missing `flush()` →
NOT-NULL `membership.user_id`, random → fixed `admin@example.com`
(EmailStr rejects reserved `.local`/`.test`); scenario auth chain
(`username` → `email`, setup is one-time 409 → login-first,
`UPCP_DISABLE_RATE_LIMIT=true` on the test env — per-IP limits would
dominate any host-local load test); `audit-events` route (was `/audit`);
agent endpoints require `X-Agent-Token` (process-wide mint, attached in
`auth_headers()`); **backend create→use(id) FK race — probe: 37/40 rows
uncommitted at 201-time → commit-before-respond in the 4 chained-create
endpoints (delivery feature/task, structure component/module)**; DB pool
now env-configurable (historical 20+10 exhausted at 50 users → test env
40+20); observability configs: file perms (10 files), tempo
`service_graphs` invalid for 2.7.x, otel `otlp/loki` endpoint must be
bare `host:port` (gRPC).

**Env gotchas:** baked images — test containers have no source mounts;
rebuild after source changes.

**Follow-ups (Queued):** dashboard/stats perf fix task; 50-user
throughput investigation; loki OTLP receiver (collector→loki:4317 refused;
top-level `otlp:` invalid in loki 3.4.2 — reverted to healthy); grafana
missing `dashboards/production` dir walk error + admin password doc
mismatch (volume initialized from root `.env`'s `admin_change_me`,
`.env.test` says `admin_test`); Lighthouse frontend perf absent from
scaffold.
