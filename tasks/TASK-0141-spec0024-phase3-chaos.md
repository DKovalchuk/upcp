# TASK-0141 — SPEC-0024 Phase 3: Chaos — run suite, MTTR + data integrity evidence

**Milestone:** SPEC-0024 (Test Environment) Phase 3
**Points:** 5
**Spec:** `specs/SPEC-0024-test-environment.md`
**Status:** DONE (closed 2026-10-18)

## Context

`tests/chaos/` scaffold exists (engine, runner, assertions, 6 scenarios +
profiles) but has **never been executed**.

## AC

- [x] `runner.py --profile quick --report` green: experiments run,
      assertions check MTTR (per `chaos_profiles.yaml` limits) + data
      integrity, markdown report produced — **3/3 PASS, EXIT=0**
- [x] `runner.py --profile full --report` green (all 7 experiments) —
      **7/7 PASS, EXIT=0**
- [x] Any script bugs found are fixed; evidence: MTTR per experiment,
      integrity verdicts, report path — see Evidence

## Evidence

**Runs** (against live test stack, seeder clean-slate before runs):
- quick: `results/chaos_20261018_063720.json` + report — 3/3 PASS
- full: `results/chaos_20261018_063954.json` + report — **7/7 PASS**
- Stack healthy after every run (app/db/redis Up+healthy post full_outage)

**MTTR per experiment (full run):** service_kill_app 6.0s ·
service_kill_db 6.0s · redis_failure 6.0s · cascade_redis_app 6.0s ·
db_restart 0.4s · app_restart 6.0s · full_outage 6.0s — all within
`chaos_profiles.yaml` limits (15–90s). Integrity verdicts: all
data-integrity + memory-stability assertions PASS (e.g. cascade 6/6,
app_restart 3/3).

**Scaffold bugs fixed (first-ever execution):**
1. `tests.chaos.*` absolute imports unreachable — repo root added to
   `sys.path` in runner
2. `ChaosVerdict` required `passed` at construction while every scenario
   assigns it afterwards → default `False`
3. Integrity probes hit `GET /api/v1/projects` without JWT → 401 failed
   every data check → `engine.get_auth_headers()` cached login
   (seeded perf admin, env-overridable)
4. Memory assertions compared pre-kill baseline vs post-restart process
   (false +242% "leak") → post-restart stability re-baseline
   (service_kill/full_outage/cascade; db_restart's app-baseline kept —
   app is not restarted there)
5. `db_restart` MTTR measured from after the 15s monitor loop → always
   ~0.0s → measured from disruption start to first healthy response
   (0.4–0.5s observed)
6. Count-parse mismatch: scenarios used `len(resp.json())` (paginated
   dict = 4 KEYS) vs assertion parsing `total` (1) → shared
   `extract_count()` on both sides
7. `mttr` undefined-name + SIM105 leftovers from fix 5 → lint clean
   (`ruff check tests/chaos/` + `ruff format` pass)

**Follow-ups:** none blocking — chaos suite ready for CI integration in
TASK-0143 (Phase 5).
