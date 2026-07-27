# Data Model — UPCP v2

## Overview

Target data model for UPCP v2. All tables use UUID v7 as primary keys, include `created_at` and `updated_at` (UTC), and soft delete via `deleted_at` where applicable.

---

## Identity & Access

### Organization
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | Identifier |
| `name` | VARCHAR(128) | Organization name |
| `slug` | VARCHAR(64) UNIQUE | URL-safe identifier |
| `settings` | JSONB | Organization settings (feature flags) |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### User
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `email` | VARCHAR(256) UNIQUE | Login email |
| `display_name` | VARCHAR(128) | Display name |
| `password_hash` | VARCHAR(256) | bcrypt hash |
| `is_active` | BOOLEAN | Whether user is active |
| `last_login_at` | TIMESTAMPTZ | Last login |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### Membership
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `user_id` | UUID FK → User | |
| `organization_id` | UUID FK → Organization | |
| `role_id` | UUID FK → Role | Role within the organization |
| `invited_by` | UUID FK → User NULL | Who invited |
| `joined_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Indexes:** UNIQUE(user_id, organization_id)

### Session
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `user_id` | UUID FK → User | |
| `token_hash` | VARCHAR(256) UNIQUE | JWT refresh token hash |
| `ip_address` | INET | IP at creation time |
| `user_agent` | TEXT | User-Agent |
| `expires_at` | TIMESTAMPTZ | |
| `revoked_at` | TIMESTAMPTZ NULL | Whether session is revoked |
| `created_at` | TIMESTAMPTZ | |

### Role
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization NULL | NULL = system role |
| `name` | VARCHAR(64) | Role name |
| `is_system` | BOOLEAN | System role (cannot be deleted) |
| `created_at` | TIMESTAMPTZ | |

### Permission
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `resource` | VARCHAR(64) | Resource (project, task, agent...) |
| `action` | VARCHAR(32) | Action (create, read, update, delete, manage) |
| `description` | TEXT | |

**Indexes:** UNIQUE(resource, action)

### RoleBinding
| Field | Type | Description |
|-------|------|-------------|
| `role_id` | UUID FK → Role | |
| `permission_id` | UUID FK → Permission | |

**Indexes:** PK(role_id, permission_id)

---

## Agent Management

### Agent
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization | |
| `name` | VARCHAR(128) | Agent name |
| `agent_type` | VARCHAR(32) | Type (claude, codex, custom) |
| `description` | TEXT | Capabilities description |
| `capabilities` | JSONB | Capabilities array |
| `is_active` | BOOLEAN | |
| `created_by` | UUID FK → User | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### AgentToken
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `agent_id` | UUID FK → Agent | |
| `token_hash` | VARCHAR(256) UNIQUE | MCP token hash |
| `name` | VARCHAR(64) | Token description |
| `expires_at` | TIMESTAMPTZ | |
| `revoked_at` | TIMESTAMPTZ NULL | |
| `last_used_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |

### AgentScope
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `agent_id` | UUID FK → Agent | |
| `allowed_operations` | JSONB | Allowed operations array |
| `max_tasks` | INT | Max concurrent tasks |
| `heartbeat_interval_sec` | INT | Heartbeat interval (default 30) |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### AgentProjectAssignment
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `agent_id` | UUID FK → Agent | |
| `project_id` | UUID FK → Project | |
| `assigned_by` | UUID FK → User | |
| `assigned_at` | TIMESTAMPTZ | |

**Indexes:** UNIQUE(agent_id, project_id)

---

## Delivery Management

### Project
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization | |
| `name` | VARCHAR(128) | |
| `slug` | VARCHAR(64) | URL-safe |
| `description` | TEXT | |
| `status` | VARCHAR(16) | active, archived |
| `settings` | JSONB | Project settings (review_policy, etc.) |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |
| `deleted_at` | TIMESTAMPTZ NULL | Soft delete |

**Indexes:** UNIQUE(organization_id, slug)

### Component
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `project_id` | UUID FK → Project | |
| `name` | VARCHAR(128) | |
| `description` | TEXT | |
| `sort_order` | INT | Display order |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### Module
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `component_id` | UUID FK → Component | |
| `name` | VARCHAR(128) | |
| `description` | TEXT | |
| `sort_order` | INT | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### Feature
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `module_id` | UUID FK → Module | |
| `title` | VARCHAR(256) | |
| `description` | TEXT | |
| `priority` | VARCHAR(16) | low, medium, high, critical |
| `status` | VARCHAR(16) | draft, ready, in_progress, done |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### Task
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `feature_id` | UUID FK → Feature | |
| `title` | VARCHAR(256) | |
| `description` | TEXT | Task description |
| `acceptance_criteria` | TEXT | Acceptance criteria |
| `state` | VARCHAR(32) | State machine state |
| `priority` | VARCHAR(16) | low, medium, high, critical |
| `estimated_effort` | VARCHAR(16) | s, m, l, xl |
| `assigned_agent_id` | UUID FK → Agent NULL | |
| `review_policy` | VARCHAR(32) | human_only, agent_then_human, agent_auto_close |
| `due_date` | DATE NULL | |
| `completed_at` | TIMESTAMPTZ NULL | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Indexes:** (feature_id, state), (assigned_agent_id, state)

---

## Agent Workflow

### TaskClaim
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `agent_id` | UUID FK → Agent | |
| `status` | VARCHAR(16) | active, released, expired, completed |
| `claimed_at` | TIMESTAMPTZ | |
| `released_at` | TIMESTAMPTZ NULL | |
| `expires_at` | TIMESTAMPTZ | Automatic expiry |

**Indexes:** UNIQUE(task_id) WHERE status='active'

### Heartbeat
| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGSERIAL PK | |
| `task_id` | UUID FK → Task | |
| `agent_id` | UUID FK → Agent | |
| `message` | TEXT NULL | Optional status message |
| `created_at` | TIMESTAMPTZ | |

**Indexes:** (task_id, created_at DESC) — for finding the latest

### Subtask
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `title` | VARCHAR(256) | |
| `status` | VARCHAR(16) | pending, in_progress, done |
| `sort_order` | INT | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### ClarificationRequest
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `agent_id` | UUID FK → Agent | |
| `question` | TEXT | Agent's question |
| `answer` | TEXT NULL | Owner's answer |
| `status` | VARCHAR(16) | open, answered, resolved, cancelled |
| `answered_by` | UUID FK → User NULL | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

---

## Quality & Evidence

### AcceptanceCriterion
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `description` | TEXT | Criterion |
| `status` | VARCHAR(16) | pending, met, not_met |
| `sort_order` | INT | |
| `created_at` | TIMESTAMPTZ | |

### DoDItem
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `project_id` | UUID FK → Project | |
| `title` | VARCHAR(256) | |
| `description` | TEXT | |
| `is_active` | BOOLEAN | |
| `sort_order` | INT | |
| `created_at` | TIMESTAMPTZ | |

### Evidence
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `agent_id` | UUID FK → Agent | |
| `evidence_type` | VARCHAR(32) | test_output, screenshot, log, file_diff, url, command_output |
| `title` | VARCHAR(256) | |
| `content` | TEXT | Content (for logs, output) |
| `url` | TEXT NULL | Link (for screenshots, URLs) |
| `metadata` | JSONB | Additional data |
| `created_at` | TIMESTAMPTZ | |

### ReviewRound
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `round_number` | INT | Round number |
| `policy` | VARCHAR(32) | Applied policy |
| `status` | VARCHAR(16) | pending, in_progress, completed, cancelled |
| `verdict` | VARCHAR(16) NULL | approved, rejected |
| `reviewer_type` | VARCHAR(16) | human, agent |
| `reviewer_id` | UUID NULL | User or Agent |
| `summary` | TEXT NULL | |
| `started_at` | TIMESTAMPTZ | |
| `completed_at` | TIMESTAMPTZ NULL | |
| `created_at` | TIMESTAMPTZ | |

### ReviewFinding
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `review_round_id` | UUID FK → ReviewRound | |
| `severity` | VARCHAR(16) | info, warning, critical |
| `category` | VARCHAR(32) | correctness, security, performance, style, missing |
| `description` | TEXT | |
| `file_path` | TEXT NULL | File (if applicable) |
| `line_number` | INT NULL | Line number |
| `status` | VARCHAR(16) | open, addressed, dismissed |
| `created_at` | TIMESTAMPTZ | |

### ContextSnapshot
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `agent_id` | UUID FK → Agent | |
| `snapshot_type` | VARCHAR(16) | start, checkpoint, completion |
| `context_data` | JSONB | Agent context |
| `created_at` | TIMESTAMPTZ | |

---

## Observability

### AuditEvent
| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGSERIAL PK | |
| `organization_id` | UUID FK → Organization | |
| `actor_type` | VARCHAR(16) | user, agent, system |
| `actor_id` | UUID | |
| `action` | VARCHAR(64) | task.created, agent.claimed... |
| `entity_type` | VARCHAR(32) | task, project, agent... |
| `entity_id` | UUID | |
| `metadata` | JSONB | Additional data |
| `ip_address` | INET NULL | |
| `created_at` | TIMESTAMPTZ | |

**Indexes:** (organization_id, created_at DESC), (entity_type, entity_id)

---

## Notifications

### Notification
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization | |
| `recipient_type` | VARCHAR(16) | user, agent |
| `recipient_id` | UUID | |
| `channel` | VARCHAR(16) | in_app, email, webhook |
| `title` | VARCHAR(256) | |
| `body` | TEXT | |
| `status` | VARCHAR(16) | pending, sent, read |
| `read_at` | TIMESTAMPTZ NULL | |
| `created_at` | TIMESTAMPTZ | |

**Indexes:** (recipient_id, status, created_at DESC)

---

## Reporting

### Report
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization | |
| `project_id` | UUID FK → Project NULL | |
| `report_type` | VARCHAR(32) | project_summary, agent_activity, delivery_status |
| `format` | VARCHAR(8) | json, pdf, csv |
| `parameters` | JSONB | Generation parameters |
| `file_path` | TEXT NULL | File path |
| `status` | VARCHAR(16) | generating, ready, failed |
| `generated_by` | UUID | User or system |
| `created_at` | TIMESTAMPTZ | |
| `expires_at` | TIMESTAMPTZ NULL | |

---

## Git Integration

### GitProvider
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization | |
| `provider_type` | VARCHAR(16) | gitlab, github, gitea |
| `base_url` | TEXT | Instance URL |
| `access_token_encrypted` | TEXT | Encrypted token |
| `webhook_secret_encrypted` | TEXT | Encrypted webhook secret |
| `is_active` | BOOLEAN | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### GitBranch
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `git_provider_id` | UUID FK → GitProvider | |
| `project_id` | UUID FK → Project | |
| `repository` | VARCHAR(256) | owner/repo |
| `branch_name` | VARCHAR(128) | |
| `last_synced_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |

**Indexes:** UNIQUE(git_provider_id, repository, branch_name)

### GitCommit
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `git_branch_id` | UUID FK → GitBranch | |
| `sha` | VARCHAR(40) | Git commit SHA |
| `message` | TEXT | |
| `author_name` | VARCHAR(128) | |
| `author_email` | VARCHAR(256) | |
| `committed_at` | TIMESTAMPTZ | |
| `synced_at` | TIMESTAMPTZ | |

**Indexes:** UNIQUE(git_branch_id, sha)

### GitLink
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID PK | |
| `git_commit_id` | UUID FK → GitCommit | |
| `entity_type` | VARCHAR(16) | task, feature |
| `entity_id` | UUID | |
| `created_at` | TIMESTAMPTZ | |

**Indexes:** (entity_type, entity_id)

---

## ER Relationships (Primary)

```
Organization 1──* User (via Membership)
Organization 1──* Project
Organization 1──* Agent
Project 1──* Component 1──* Module 1──* Feature 1──* Task
Task 1──* TaskClaim
Task 1──* Heartbeat
Task 1──* Subtask
Task 1──* ClarificationRequest
Task 1──* Evidence
Task 1──* ReviewRound 1──* ReviewFinding
Task 1──* AcceptanceCriterion
Task 1──* ContextSnapshot
Agent 1──* AgentToken
Agent 1──* AgentScope
Agent *──* Project (via AgentProjectAssignment)
GitProvider 1──* GitBranch 1──* GitCommit 1──* GitLink
```
