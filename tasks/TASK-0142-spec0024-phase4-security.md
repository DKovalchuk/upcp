# TASK-0142 — SPEC-0024 Phase 4: Security — ZAP DAST, API fuzzer, auth tests, Kali

**Milestone:** SPEC-0024 (Test Environment) Phase 4
**Points:** 13
**Spec:** `specs/SPEC-0024-test-environment.md` (Security: SAST + DAST
baseline/scheduled + pentest agent in Kali + ACP, frontend security as
separate suite). Note: full design doc
`docs/planning/TEST_ENVIRONMENT_SPEC.md` is MISSING (never in git) —
design decisions will need task-level mini-spec or doc reconstruction.
**Status:** PENDING

## Context

`docker-compose.test.yml` provides `zap` and `kali` services, but there is
NO `tests/security/` directory — this phase is real build work.

## AC (draft — refine when starting)

- [ ] ZAP DAST baseline scan against test app → report artifact
- [ ] API fuzzer scenario suite (auth bypass, injection, malformed input)
- [ ] Auth/RBAC security test suite (automated, pytest-compatible)
- [ ] Kali pentest agent run (or documented ACP approach) → findings
- [ ] Reports actionable (markdown/JSON), Grafana-visualizable

## Evidence

(to be filled)
