# TASK-0102 — M16 Sprint 3: Analytics Service + API

**Spec:** SPEC-0019
**Milestone:** M16
**Sprint:** S18.3
**Status:** PENDING
**Size:** L

## Objective

Implement analytics service with project trends, agent performance, team velocity, and health history.

## Acceptance Criteria

- [ ] AnalyticsService with 4 methods: get_project_trends, get_agent_performance, get_team_velocity, get_health_history
- [ ] GET /analytics/project/{id}/trends — task completion rate over time
- [ ] GET /analytics/agent/{id}/performance — tasks completed, success rate, avg time
- [ ] GET /analytics/project/{id}/velocity — tasks completed per week
- [ ] GET /analytics/project/{id}/health-history — health score over time
- [ ] GET /analytics/agents/overview — all agents summary
- [ ] Pagination on list endpoints
- [ ] All existing tests pass
- [ ] New tests: 6 service tests + 5 API tests

## Implementation Plan

### Step 1: AnalyticsService
- `backend/app/reporting/analytics.py`
- Methods query Task, TaskClaim, ReviewRound, Evidence tables
- Return time-series data for charts

### Step 2: Analytics API
- `backend/app/api/v1/analytics.py`
- 5 endpoints with pagination

### Step 3: Tests
- `backend/tests/test_analytics.py`

## Files to Create/Modify

| File | Action |
|------|--------|
| `backend/app/reporting/analytics.py` | CREATE |
| `backend/app/api/v1/analytics.py` | CREATE |
| `backend/app/main.py` | MODIFY — register router |
| `backend/tests/test_analytics.py` | CREATE |
