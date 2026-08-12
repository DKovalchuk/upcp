# TASK-0113 — M19 S21.2: Service-Layer Tests

**Milestone:** M19
**Sprint:** S21.2
**Status:** IN PROGRESS
**Spec:** SPEC-0022
**Estimate:** 8pts

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
