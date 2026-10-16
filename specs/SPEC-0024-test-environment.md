# SPEC-0024: Test Environment — Comprehensive Quality Gate

> Status: Approved | Created: 2026-08-18 | Owner: Dmitry

## Overview

Test environment (`test`) becomes the quality gate between dev/stage and production readiness.
Three pillars: Performance, Chaos Engineering, Security Testing.

## Decisions

| Aspect | Decision |
|--------|----------|
| Priority | All 3 modules parallel |
| Automation | Nightly + on merge to test branch |
| Load testing | Locust (Python), all endpoints + frontend (Lighthouse) |
| Concurrency | Full suite: claim races, heartbeats, parallel creates, uploads, rate limit storms |
| MCP | Separate scenario + in mixed workload |
| Chaos | All components, cascade failures, full assertions |
| Security | SAST + DAST (baseline + scheduled full) + pentest agent in Kali Docker + ACP |
| Kali | Docker container kalilinux/kali-rolling + ACP agent + full toolset |
| Frontend security | Separate test suite |
| Reports | Markdown + JSON + Grafana + HTML (Allure-style) |
| Grafana | 8 dashboards: 4 existing + 4 test-specific, separate folder |
| Resources | CPU, Memory, Disk IO, Network, DB pool, Redis stats, PG stats |
| Regression | Comparison without strict thresholds (human decides) |
| Seeder | Clean slate + seed before each test |
| Versioning | Git (JSON results in repo) |
| Data volume | Progressive: x1, x10, x100 |

## Full Spec

See `docs/planning/TEST_ENVIRONMENT_SPEC.md` for complete architecture, scenarios, and implementation details.

## Milestones

- Phase 1 (S1): Foundation — docker-compose, metrics, seeder, basic Locust
- Phase 2 (S2): Performance — all Locust scenarios, SLI/SLO, analyzer, Grafana
- Phase 3 (S3): Chaos — Docker chaos scripts, assertions, runner
- Phase 4 (S4): Security — ZAP DAST, API fuzzer, auth tests, Kali pentest agent
- Phase 5 (S5): Integration — aggregate reporter, CI/CD, docs

## Exit Criteria

- All services healthy in test compose
- Locust scenarios cover all API endpoints
- Chaos experiments measure MTTR + data integrity
- Security scans produce actionable reports
- Grafana dashboards visualize all test results
- CI/CD triggers tests on schedule and events
