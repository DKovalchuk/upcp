# Audit Events — UPCP v2

> Scope: `security` / `audit` | Version: 2.0.0

## 1. Overview

All significant actions in UPCP are recorded in an immutable audit log.
Audit events are used for incident investigation, compliance, and monitoring.

## 2. Event Format

```json
{
  "id": "evt_a1b2c3d4",
  "timestamp": "2026-07-27T10:30:00.123Z",
  "event_type": "auth.login.success",
  "severity": "info",
  "actor": {
    "type": "user",
    "id": "usr_x1y2z3",
    "email": "user@example.com",
    "ip": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  },
  "resource": {
    "type": "session",
    "id": "ses_a1b2c3"
  },
  "context": {
    "project_id": "proj_x1y2z3",
    "organization_id": "org_a1b2c3"
  },
  "details": {},
  "metadata": {
    "request_id": "req_a1b2c3",
    "duration_ms": 45
  }
}
```

### 2.1 Required Fields

| Field         | Description                                 |
|---------------|---------------------------------------------|
| `id`          | Event UUID                                  |
| `timestamp`   | ISO 8601, UTC                               |
| `event_type`  | Hierarchical name (dot-separated)           |
| `severity`    | `info`, `warning`, `critical`               |
| `actor`       | Who performed the action                    |
| `resource`    | What was acted upon                         |

### 2.2 Severity Levels

| Level     | Description                                       |
|-----------|---------------------------------------------------|
| `info`    | Normal operations                                 |
| `warning` | Suspicious but acceptable operations              |
| `critical`| Security violations, lockouts                     |

## 3. Authentication Events

| Event Type                        | Severity  | Description                             |
|----------------------------------|-----------|-----------------------------------------|
| `auth.login.success`             | info      | Successful login                        |
| `auth.login.failed`              | warning   | Failed login attempt                    |
| `auth.login.blocked`             | critical  | Login blocked (brute-force)             |
| `auth.logout`                    | info      | User logged out                         |
| `auth.token.refresh`             | info      | Access token refreshed                  |
| `auth.token.created`             | info      | New refresh token created               |
| `auth.token.revoked`             | info      | Token revoked                           |
| `auth.token.reuse_detected`      | critical  | Reuse of a revoked token detected       |
| `auth.password.changed`          | info      | Password changed                        |
| `auth.password.reset_requested`  | info      | Password reset requested                |
| `auth.password.reset_completed`  | info      | Password reset completed                |
| `auth.account.locked`            | warning   | Account locked                          |
| `auth.account.unlocked`          | info      | Account unlocked                        |
| `auth.account.deactivated`       | warning   | Account deactivated                     |
| `auth.account.activated`         | info      | Account activated                       |
| `auth.setup.completed`           | info      | First-run setup completed               |

### 3.1 Details for Auth Events

```json
// auth.login.failed
{
  "reason": "invalid_password",
  "attempt_number": 3,
  "lockout_threshold": 5
}

// auth.token.reuse_detected
{
  "token_family": "fam_a1b2c3",
  "revoked_tokens_count": 5,
  "first_used_at": "2026-07-27T10:00:00Z"
}
```

## 4. Agent Events

| Event Type                        | Severity  | Description                             |
|----------------------------------|-----------|-----------------------------------------|
| `agent.token.created`            | info      | Agent token created                     |
| `agent.token.revoked`            | info      | Agent token revoked                     |
| `agent.token.rotated`            | info      | Agent token rotated                     |
| `agent.token.expired`            | info      | Agent token expired                     |
| `agent.task.claimed`             | info      | Agent claimed task                      |
| `agent.task.released`            | info      | Agent released task                     |
| `agent.task.submitted`           | info      | Agent submitted result                  |
| `agent.task.approved`            | info      | Result approved                         |
| `agent.task.rejected`            | info      | Result rejected                         |
| `agent.task.timeout`             | warning   | Task execution timeout                  |
| `agent.heartbeat`                | info      | Agent heartbeat                         |
| `agent.heartbeat.stale`          | warning   | Agent not responding (>7 min)           |
| `agent.clarification.requested`  | info      | Agent requested clarification           |
| `agent.clarification.provided`   | info      | Clarification provided                  |
| `agent.evidence.submitted`       | info      | Agent uploaded evidence                 |
| `agent.review.requested`         | info      | Review requested                        |
| `agent.review.completed`         | info      | Review completed                        |
| `agent.file.created`             | info      | Agent created file                      |
| `agent.file.modified`            | info      | Agent modified file                     |
| `agent.mcp.tool_called`          | info      | MCP tool called                         |
| `agent.mcp.tool_denied`          | warning   | MCP tool blocked                        |
| `agent.scope.denied`             | warning   | Out-of-scope access attempt             |
| `agent.rate_limit.exceeded`      | warning   | Rate limit exceeded                     |

### 4.1 Details for Agent Events

```json
// agent.task.claimed
{
  "task_id": "tsk_a1b2c3",
  "agent_token_id": "agp_proj1_abc",
  "role": "agent_builder",
  "previous_status": "pending"
}

// agent.scope.denied
{
  "attempted_action": "project.settings.update",
  "required_scope": "proj:admin",
  "actual_scope": "proj:member",
  "target_project_id": "proj_x1y2z3"
}
```

## 5. Administration Events

| Event Type                              | Severity  | Description                         |
|----------------------------------------|-----------|-------------------------------------|
| `admin.role.assigned`                  | warning   | Role assigned                       |
| `admin.role.revoked`                   | warning   | Role revoked                        |
| `admin.user.created`                   | info      | User created                        |
| `admin.user.deactivated`               | warning   | User deactivated                    |
| `admin.user.activated`                 | info      | User activated                      |
| `admin.project.created`                | info      | Project created                     |
| `admin.project.deleted`                | critical  | Project deleted                     |
| `admin.project.settings.changed`       | warning   | Project settings changed            |
| `admin.organization.created`           | info      | Organization created                |
| `admin.organization.deleted`           | critical  | Organization deleted                |
| `admin.organization.settings.changed`  | warning   | Organization settings changed       |
| `admin.integration.added`              | warning   | Integration added                   |
| `admin.integration.removed`            | warning   | Integration removed                 |
| `admin.secret.rotated`                 | warning   | Secret rotated                      |
| `admin.backup.created`                 | info      | Backup created                      |
| `admin.backup.restored`                | critical  | Restored from backup                |

## 6. System Events

| Event Type                        | Severity  | Description                             |
|----------------------------------|-----------|-----------------------------------------|
| `system.startup`                  | info      | Application started                     |
| `system.shutdown`                 | info      | Application stopped                     |
| `system.config.changed`           | warning   | Configuration changed                   |
| `system.error.unhandled`          | critical  | Unhandled error                         |
| `system.rate_limit.abuse`         | critical  | Abuse detected                          |
| `system.ip.blocked`               | critical  | IP blocked                              |

## 7. Storage and Retention

### 7.1 Storage

- Primary: PostgreSQL table `audit_events`
- Partitioning: by month (`audit_events_2026_07`)
- Indexes: `timestamp`, `event_type`, `actor.id`, `resource.id`

### 7.2 Retention

- Active partition: current month + next
- Hot storage retention: 12 months
- Archive: compressed partitions in object storage (S3/MinIO)
- Deletion: on owner request (GDPR compliance)

### 7.3 Immutability

- Audit events — append-only (no UPDATE/DELETE)
- Write permissions: audit service account only
- Read permissions: Admin, Owner
- Integrity: hash chain (each event includes the hash of the previous one)

## 8. Querying the Audit Log

```
GET /api/v1/audit-events
  ?event_type=auth.login.failed
  &actor_id=usr_x1y2z3
  &from=2026-07-01T00:00:00Z
  &to=2026-07-27T23:59:59Z
  &severity=critical
  &limit=50
  &cursor=evt_a1b2c3
```

- Pagination: cursor-based
- Filters: event_type, actor_id, resource_id, severity, date range
- Export: CSV, JSON (up to 10,000 records per request)
