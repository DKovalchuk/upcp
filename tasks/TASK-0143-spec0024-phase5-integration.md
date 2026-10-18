# TASK-0143 — SPEC-0024 Phase 5: Integration — quality gate in CI, aggregate reporter, docs

**Milestone:** SPEC-0024 (Test Environment) Phase 5
**Points:** 8
**Spec:** `specs/SPEC-0024-test-environment.md` (Nightly + on-merge
triggers; reports Markdown + JSON; regression comparison without strict
thresholds; results versioning). Grafana dashboard ingestion explicitly
deferred (recorded in TASK-0142 deviations).
**Status:** IN PROGRESS (started 2026-10-18; implementation complete and
fully rehearsed locally — MR open; post-merge steps remain: schedule
creation, develop + schedule pipeline observations, phase-B hard-gate
flip)

## Mini-spec (design decisions — agreed with Dmitry 2026-10-18)

### Tiering (what runs where)

| Tier | Trigger | Content |
|------|---------|---------|
| MR | merge_request_event | unchanged (lint/typecheck/unit/vitest/SAST) — no heavy stacks |
| develop-merge | push develop | **quality gate**: e2e (root + frontend), chaos quick, security baseline, perf smoke — ephemeral stack; blocks deploy once flipped to hard gate (stage order lint→test→quality→build→deploy) |
| Nightly | pipeline schedule (~03:00, develop) | **full**: chaos full, security full (ZAP+Kali), perf load (allow_failure forever), e2e |
| On demand | run the schedule from GitLab UI, or run locally (docs §6) | no dedicated manual job (deviation below) |

### Failure policy (two phases)

Phase A (this MR): `quality:gate` starts with `allow_failure: true` —
first observations in the CI environment. Phase B (follow-up commit
**within this task**): after ≥2 green develop + ≥1 green schedule runs
observed → flip verified-green jobs to hard gate. `perf load` never gates
(honest red SLO until TASK-0140 throughput findings are fixed); perf RC
counts toward the gate only on the `quick` profile.

### Environments (full tables in docs/ops/environments.md)

dev (local `upcp` / CI `upcp-dev`, own ports 3073/38083/35435/36384, own
data dirs) · test (local `upcp-test` + mandatory `--env-file .env.test` /
**CI ephemeral hermetic `upcp-test-ci`** via `.env.ci`, teardown in
after_script) · stage (`upcp-stage`, sole owner = deploy:stage) ·
**prod — future model documented only, never touched**. Environment urls
fixed: dev → 3073, stage → 3070 (both were stale 3080).

### Mechanics (docs/ops/ci-quality-gates.md §3)

One quality job per tier (setup + suites + aggregate + teardown — GitLab
docker-executor gives every job a fresh checkout, so a job chain would
bind-mount stale workspaces). All suites run **inside the gate network**
(job joins via `docker network connect` — host loopback is unreachable
from job containers, the deploy-probe incident). Env contract:
`SECURITY/CHAOS_BASE_URL`+`LOCUST_HOST` → `http://app:8080`; root e2e →
`http://nginx` + `E2E_API_BASE=http://app:8080`; frontend e2e → own vite
+ `VITE_API_URL=http://app:8080`; credentials via `E2E_ADMIN_PASSWORD`
(dev default `admin123`, gate passes `TestAdmin123!`); authz DB fixture
via `SECURITY_DB_PORT=35436`. e2e runs in the playwright container
(uid 1000, `HOME=/tmp`). Reporter: `tests/quality_gate/aggregate.py` →
`quality-report.{md,json}`.

## AC

- [x] Hermetic CI stack support: `.env.ci` (ports/project), env-driven
      compose data dirs (test + stage), `e2e` service (profile ci) —
      proven by a full local gate rehearsal against `--env-file .env.ci`
      (build → up → health → seed → suites → aggregate → down; other
      stacks verified untouched)
- [x] `quality:gate` job: stack up → seed → suites (e2e ×2, chaos quick,
      security baseline, perf smoke) → `quality-report.{md,json}` +
      suite artifacts → teardown always, phase-A `allow_failure: true` —
      every step rehearsed locally with the exact CI invocations;
      CI Lint `valid: true, errors: []`
- [ ] Nightly schedule: `workflow.rules` += schedule **[x]**; schedule
      created via API + first `full` run observed **[ ] — post-merge**
- [x] Aggregate reporter with unit tests (red→green, 10 tests) incl.
      regression-vs-baseline section; runs as gate step 1 (unit) and
      step 5 (report)
- [x] Deploy topology split: deploy:dev own project/ports/group/url,
      deploy:stage sole owner of upcp-stage; both `environment.url`s
      corrected; validated via CI Lint + `config` simulations
      (dev-env → `upcp-dev`:38083; clean-env stage → `upcp-stage`
      38081/35433/3070/36382 + `./data/postgres-stage` unchanged)
- [x] e2e baseURL + credential parameterization — defaults unchanged:
      dev-stack runs **22/22** (root) and **153/153** (frontend);
      gate-container runs **22/22** and **153/153** with envs set
- [ ] Two-phase flip to hard gate — post-merge (≥2 green develop + ≥1
      green schedule runs observed); perf load stays allow_failure
- [x] Docs written + INDEX updated (`docs/ops/environments.md`,
      `docs/ops/ci-quality-gates.md`)
- [ ] Spec exit criteria end-to-end (CI/CD triggers tests on schedule
      and events): evidence = first green develop gate + first green
      schedule run + report artifact — **post-merge**

## Evidence

**Full local gate rehearsal (ephemeral `upcp-test-ci`, exact CI
invocations) — all green:**
- reporter unit tests → **10 passed**; `aggregate.py` → **RC=0**
  (`quality-report.{md,json}`, suites ok 3/3)
- health 200 (in-container probe), seed clean-slate RC=0
- **root e2e in playwright container: 22 passed RC=0**
  (`E2E_API_BASE=http://app:8080 E2E_ADMIN_PASSWORD=TestAdmin123!`)
- **frontend e2e in container: 153 passed RC=0** (own vite +
  `VITE_API_URL=http://app:8080`)
- chaos quick **3/3 RC=0** (`CHAOS_COMPOSE_PROJECT=upcp-test-ci`)
- security baseline **RC=0**: authz 52/55 (+3 documented xfail findings),
  fuzz 55/55, zap 2/2 (`SECURITY_DB_PORT=35436`)
- perf smoke **RC=0**, SLO 363/363 (+41 deviations vs old baseline →
  regression section, human-review only)
- teardown: no `upcp-test-ci` containers/networks left; dev/stage/local
  test stacks untouched (6 containers still Up)

**Validation:** CI Lint `valid` (final yaml incl. all e2e envs) ·
`compose config --quiet` OK · deploy:dev/stage config simulations as
above · `ruff check tests/` clean repo-wide (incl. drive-by I001 fix in
`tests/performance/runner.py`) · frontend oxlint 0 errors · backend
untouched this task (tsc has 3 pre-existing unrelated errors).

**Wiring bugs found & fixed during rehearsal (each reproduced first):**
1. gate script would have used **dev** compose file (no `-f`) →
   `COMPOSE_FILE` job variable pins the test stack everywhere incl.
   nested wrapper invocations
2. authz RBAC fixtures hit the **wrong DB** (default 35434 = local test
   stack, gate is 35436) → 3 failed (49/55) → `SECURITY_DB_PORT=35436`
   → 52/55
3. `nginx.test.conf` lacked the **`/auth` location** — SPA same-origin
   login at `http://nginx` fell through to static frontend → added
4. e2e container `HOME=/home/pwuser` unwritable (pwuser is uid **1001**,
   home 750; service runs as uid 1000) → `HOME=/tmp`
5. e2e specs hardcoded `admin123` (**dev-stack** cred) vs seeded test
   stack `TestAdmin123!` → `E2E_ADMIN_PASSWORD` env, 7 positive logins,
   defaults unchanged
6. local `frontend/node_modules` root-owned rot blocked `npm ci`
   (EACCES) → wiped via privileged container, rebuilt uid-1000 by the
   gate's own npm ci (project memory updated)

**Commits (atomic, one concern each):** `9f7e053` hermetic stack ·
`0f5e54f` aggregate reporter · `ef16f19` e2e parameterization ·
`d4c6157` CI gate + schedule rules + deploy split · `394274c` rehearsal
evidence + lint fix · `86cee9c` docs · + this status commit.

## Deviations

- **Grafana**: quality-report JSON is the integration point; no new
  dashboard added (deferred per TASK-0142).
- **Manual tier**: no dedicated manual job — "run schedule from UI /
  run locally" instead of a duplicate stack job (docs §1).
- **Results versioning**: raw JSON/CSV = local + CI artifacts (30d);
  markdown reports + perf baselines tracked in git — deviates from the
  spec's "JSON results in repo" (docs §4).
- **Docs §7** ("schedule not yet created") is accurate at MR time —
  refresh it in the phase-B finalization commit after the schedule
  exists.

## Follow-ups

- Post-merge: create schedule (API) → observe develop gate → observe
  schedule run → phase-B flip commit → docs §7 refresh → task DONE +
  PROJECT_STATUS.
