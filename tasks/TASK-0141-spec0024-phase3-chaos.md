# TASK-0141 — SPEC-0024 Phase 3: Chaos — run suite, MTTR + data integrity evidence

**Milestone:** SPEC-0024 (Test Environment) Phase 3
**Points:** 5
**Spec:** `specs/SPEC-0024-test-environment.md`
**Status:** PENDING (blocked by TASK-0140 — same test stack, seeder
clean-slate rule makes concurrent perf/chaos runs unsafe)

## Context

`tests/chaos/` scaffold exists (engine, runner, assertions, 6 scenarios +
profiles) but has **never been executed**.

## AC

- [ ] `runner.py --profile quick --report` green: experiments run,
      assertions check MTTR (per `chaos_profiles.yaml` limits) + data
      integrity, markdown report produced
- [ ] `runner.py --profile full --report` green (all 7 experiments)
- [ ] Any script bugs found are fixed; evidence: MTTR per experiment,
      integrity verdicts, report path

## Evidence

(to be filled)
