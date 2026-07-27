# SPEC-0016 Human Control UX, Project Drill-down & Portfolio Insights

Status: draft
Owner: project-owner
Milestone: M11
Related tasks: TASK-0083 through TASK-0088

## Problem

Dashboard is vanity statistics. No action-oriented view. No deep navigation from portfolio to task. No notifications.

## Goal

1. Attention Dashboard — action-oriented view showing items needing review, open questions, blocked tasks, stale claims.
2. Project Drill-down — deep navigation with URL-synced state (breadcrumbs, tabs, deep links).
3. Notifications — in-app notification system for agent actions.
4. Reporting Insights — project health scores and portfolio overview.

## Requirements

### Attention Dashboard API

- GET /dashboard/attention — aggregated attention items:
  - needs_review: tasks with pending review rounds
  - open_questions: blocking clarification requests
  - blocked_tasks: tasks in blocked status
  - stale_claims: claims without heartbeat > 7min
  - failed_dod: tasks with failed DoD items
  - rejected_tasks: tasks with reject verdict
  - agent_verdicts_waiting: agent verdicts awaiting human confirmation
  - low_health_projects: projects with health score < 70
  - recent_activity: last 10 agent actions

### Project Health Score

```
health = 100
  - (blocked_tasks * 15)
  - (stale_claims * 10)
  - (failed_dod * 10)
  - (open_clarifications * 5)
  - (rejected_tasks * 10)
```

### Attention Dashboard Frontend

- Summary cards at top (counts with click-to-filter)
- Two-column layout: left = action items, right = activity + health
- Auto-refresh every 30s via TanStack Query
- Click items → task detail sheet

### Notifications

- Notification model: id, user_id, type, title, message, entity_type, entity_id, is_read, created_at
- API: GET /notifications, PATCH /notifications/{id}/read, POST /notifications/read-all
- Created by workflow actions (claim, heartbeat, evidence, review)
- Badge count in top bar

### Reporting Insights

- GET /projects/{id}/health — project health score breakdown
- GET /portfolio/overview — aggregate stats across all projects

## Acceptance Criteria

- Attention dashboard API returns correct aggregated data.
- Frontend dashboard shows action items with proper layout.
- Notification model and API.
- Notifications created on workflow events.
- Project health score calculated correctly.
- Tests for all new endpoints.
- TypeScript compiles, tests pass.

## DoD

- Spec approved.
- All endpoints implemented with TDD.
- Frontend components functional.
- Tests pass, lint passes.
