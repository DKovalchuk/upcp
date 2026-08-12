# SPEC-0019 — M16: Notifications & Reporting

**Milestone:** M16
**Version:** 0.18.0
**Status:** PLANNED
**Created:** 2026-08-12

## 1. Problem

M15 completed the Agent Workflow (claim, heartbeat, clarification, evidence, review), but:
- Notifications are only created manually — no auto-generation from workflow events
- No external notification channels (email, webhook) — users only see in-app notifications
- Reports exist but lack analytics — no trends, no agent performance, no health history

## 2. Scope

### In Scope (3 components, 5 tasks)

| # | Component | Tasks | Description |
|---|-----------|-------|-------------|
| 1 | Notification System | 1 | Auto-generate notifications from workflow events |
| 2 | Notification Channels | 2 | Email channel + webhook channel |
| 3 | Reports & Analytics | 2 | Analytics dashboard + agent performance reports |

### Out of Scope
- Slack/Teams integration (future)
- SMS notifications (future)
- Notification preferences per user (future)
- Real-time WebSocket notifications (future)

## 3. Component Details

### 3.1 Notification System — Auto-Generation

**Goal:** Notifications are automatically created when workflow events occur.

**Events to notify:**
- Task claimed by agent → notify task owner
- Clarification asked → notify task assignee
- Clarification answered → notify asker
- Evidence attached → notify reviewer
- Review completed → notify task assignee
- Review rejected → notify agent
- Stale claim detected → notify admin
- Task status changed → notify watchers

**Implementation:**
- `NotificationTrigger` service that creates notifications from events
- Hook into existing services (TaskService, EvidenceService, ReviewRoundService)
- Event types: `task.claimed`, `clarification.asked`, `clarification.answered`, `evidence.attached`, `review.completed`, `review.rejected`, `claim.stale`, `task.status_changed`

**API:**
- POST `/notifications` — create notification (internal use)
- Existing endpoints remain unchanged

### 3.2 Notification Channels — Email

**Goal:** Send notifications via email when configured.

**Implementation:**
- `EmailChannel` class implementing `NotificationChannel` interface
- SMTP configuration via environment variables (`UPCP_SMTP_HOST`, `UPCP_SMTP_PORT`, `UPCP_SMTP_USER`, `UPCP_SMTP_PASS`)
- Email templates for each notification type
- Async sending via background task (no blocking)

**API:**
- POST `/notification-channels` — register channel
- GET `/notification-channels` — list channels
- DELETE `/notification-channels/{id}` — remove channel

### 3.3 Notification Channels — Webhook

**Goal:** Send notifications via HTTP webhook.

**Implementation:**
- `WebhookChannel` class implementing `NotificationChannel` interface
- Configurable URL, headers, retry policy
- HMAC signature for verification

**API:**
- Same as Email channel (shared CRUD)

### 3.4 Reports & Analytics — Dashboard

**Goal:** Analytics dashboard showing project health trends, agent performance, task velocity.

**Implementation:**
- `AnalyticsService` with methods:
  - `get_project_trends(project_id, days)` — task completion rate over time
  - `get_agent_performance(agent_id, days)` — tasks completed, success rate, avg time
  - `get_team_velocity(project_id, days)` — tasks completed per week
  - `get_health_history(project_id, days)` — health score over time

**API:**
- GET `/analytics/project/{id}/trends` — project trends
- GET `/analytics/agent/{id}/performance` — agent performance
- GET `/analytics/project/{id}/velocity` — team velocity
- GET `/analytics/project/{id}/health-history` — health history

### 3.5 Reports & Analytics — Agent Performance

**Goal:** Dedicated agent performance reports.

**Implementation:**
- Agent performance card with metrics
- Tasks completed, success rate, avg completion time
- Clarification rate, evidence quality score
- Review verdict distribution

**API:**
- GET `/analytics/agents/overview` — all agents summary
- GET `/analytics/agent/{id}/detail` — detailed agent report

## 4. Database Changes

### New Tables

```sql
-- Notification channel configuration
CREATE TABLE notification_channel (
    id VARCHAR(36) PRIMARY KEY,
    channel_type VARCHAR(50) NOT NULL,  -- email, webhook
    name VARCHAR(255) NOT NULL,
    config JSON NOT NULL,               -- channel-specific config
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notification delivery log
CREATE TABLE notification_delivery (
    id VARCHAR(36) PRIMARY KEY,
    notification_id VARCHAR(36) REFERENCES notification(id),
    channel_id VARCHAR(36) REFERENCES notification_channel(id),
    status VARCHAR(20) NOT NULL,        -- pending, sent, failed
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Migration: 0019_add_notification_channels

## 5. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/notification-channels` | Create channel |
| GET | `/api/v1/notification-channels` | List channels |
| DELETE | `/api/v1/notification-channels/{id}` | Delete channel |
| POST | `/api/v1/notification-channels/{id}/test` | Test channel |
| GET | `/api/v1/analytics/project/{id}/trends` | Project trends |
| GET | `/api/v1/analytics/agent/{id}/performance` | Agent performance |
| GET | `/api/v1/analytics/project/{id}/velocity` | Team velocity |
| GET | `/api/v1/analytics/project/{id}/health-history` | Health history |
| GET | `/api/v1/analytics/agents/overview` | All agents overview |

## 6. Frontend Changes

### New Pages
- `/analytics` — Analytics dashboard with charts
- `/analytics/agent/:id` — Agent performance detail

### New Components
- `NotificationChannelSettings` — Settings page for channel config
- `AnalyticsDashboard` — Main analytics view with tabs
- `AgentPerformanceCard` — Agent metrics card
- `TrendChart` — Recharts line chart for trends
- `VelocityChart` — Bar chart for team velocity

### Updated Components
- `NotificationBell` — Show channel delivery status
- `SettingsPage` — Add notification channels tab

## 7. Testing

### Backend Tests
- NotificationTrigger: 8 tests (one per event type)
- EmailChannel: 3 tests (send, config validation, error handling)
- WebhookChannel: 3 tests (send, HMAC, retry)
- AnalyticsService: 6 tests (trends, performance, velocity, health)
- API endpoints: 9 tests (CRUD + analytics)

### Frontend Tests
- AnalyticsDashboard: 3 tests (loading, empty, data display)
- AgentPerformanceCard: 2 tests
- NotificationChannelSettings: 3 tests
- TrendChart: 2 tests

## 8. Definition of Done

- [ ] Notifications auto-generated from all 8 workflow events
- [ ] Email channel sends notifications via SMTP
- [ ] Webhook channel sends notifications via HTTP
- [ ] Analytics dashboard shows project trends
- [ ] Agent performance report shows metrics
- [ ] All existing tests pass (695 be + 260 fe)
- [ ] New tests pass (37 be + 10 fe)
- [ ] Lint passes
- [ ] Type check passes
- [ ] Docs updated
