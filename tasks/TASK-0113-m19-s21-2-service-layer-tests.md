# TASK-0113 — M19 S21.2: Service-Layer Tests

**Milestone:** M19
**Sprint:** S21.2
**Status:** DONE
**Spec:** SPEC-0022
**Estimate:** 8pts

**Audit 2026-10-24 (evidence):** все AC закрыты: `test_delivery_service.py`
(29 тестов), `test_quality_service.py` (34), `test_reporting_service.py` (26),
`test_lifecycle_integration.py` (6) — все существуют и проходят. Общий
инфраструктурный engine из `tests/conftest.py` (`_test_engine`/`_TestSession`,
40 файлов используют) — engine-dedup соблюдён.
**Отклонение по AC6 (minor):** delivery/reporting/lifecycle используют фикстуру
`db_session` напрямую, `test_quality_service.py` оборачивает общий
`_TestSession` в локальные фикстуры (`session`, `project`, `feature`) — общий
engine, но не сам `db_session`. Движок не дублируется — принято как
соответствие интенту AC.
Evidence: targeted pytest 130 passed (2026-10-24), CI 465-469 green.

## Objective

Add unit tests for core service-layer business logic (delivery, quality, reporting) and a full lifecycle integration test.

## Acceptance Criteria

- [ ] `delivery/service.py` unit tests (FeatureService, TaskService, SubtaskService)
- [ ] `quality/service.py` unit tests (EvidenceService, ReviewRoundService, QualityGateService)
- [ ] `reporting/service.py` unit tests (ReportService, NotificationService)
- [ ] Full lifecycle integration test (project → feature → task → evidence → review → complete)
- [ ] All existing tests continue to pass
- [ ] New tests use shared `db_session` fixture from conftest.py

## Implementation Plan

1. **delivery/service tests** — FeatureService CRUD, TaskService CRUD + complete, SubtaskService CRUD
2. **quality/service tests** — EvidenceService transitions, ReviewRoundService flow, QualityGateService DoD
3. **reporting/service tests** — ReportService daily generation, NotificationService CRUD
4. **lifecycle integration test** — End-to-end: create project → feature → task → submit evidence → review → complete
