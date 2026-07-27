# Data Model — UPCP v2

## Обзор

Целевая модель данных UPCP v2. Все таблицы используют UUID v7 в качестве первичных ключей, включают `created_at` и `updated_at` (UTC), soft delete через `deleted_at` где применимо.

---

## Identity & Access

### Organization
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | Идентификатор |
| `name` | VARCHAR(128) | Название организации |
| `slug` | VARCHAR(64) UNIQUE | URL-safe идентификатор |
| `settings` | JSONB | Настройки организации (feature flags) |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### User
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `email` | VARCHAR(256) UNIQUE | Email для входа |
| `display_name` | VARCHAR(128) | Отображаемое имя |
| `password_hash` | VARCHAR(256) | bcrypt hash |
| `is_active` | BOOLEAN | Активен ли пользователь |
| `last_login_at` | TIMESTAMPTZ | Последний вход |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### Membership
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `user_id` | UUID FK → User | |
| `organization_id` | UUID FK → Organization | |
| `role_id` | UUID FK → Role | Роль в организации |
| `invited_by` | UUID FK → User NULL | Кто пригласил |
| `joined_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Индексы:** UNIQUE(user_id, organization_id)

### Session
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `user_id` | UUID FK → User | |
| `token_hash` | VARCHAR(256) UNIQUE | Hash JWT refresh token |
| `ip_address` | INET | IP при создании |
| `user_agent` | TEXT | User-Agent |
| `expires_at` | TIMESTAMPTZ | |
| `revoked_at` | TIMESTAMPTZ NULL | Отозвана ли сессия |
| `created_at` | TIMESTAMPTZ | |

### Role
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization NULL | NULL = system role |
| `name` | VARCHAR(64) | Название роли |
| `is_system` | BOOLEAN | Системная роль (нельзя удалить) |
| `created_at` | TIMESTAMPTZ | |

### Permission
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `resource` | VARCHAR(64) | Ресурс (project, task, agent...) |
| `action` | VARCHAR(32) | Действие (create, read, update, delete, manage) |
| `description` | TEXT | |

**Индексы:** UNIQUE(resource, action)

### RoleBinding
| Поле | Тип | Описание |
|------|-----|----------|
| `role_id` | UUID FK → Role | |
| `permission_id` | UUID FK → Permission | |

**Индексы:** PK(role_id, permission_id)

---

## Agent Management

### Agent
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization | |
| `name` | VARCHAR(128) | Имя агента |
| `agent_type` | VARCHAR(32) | Тип (claude, codex, custom) |
| `description` | TEXT | Описание возможностей |
| `capabilities` | JSONB | Массив capabilities |
| `is_active` | BOOLEAN | |
| `created_by` | UUID FK → User | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### AgentToken
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `agent_id` | UUID FK → Agent | |
| `token_hash` | VARCHAR(256) UNIQUE | Hash MCP-токена |
| `name` | VARCHAR(64) | Описание токена |
| `expires_at` | TIMESTAMPTZ | |
| `revoked_at` | TIMESTAMPTZ NULL | |
| `last_used_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |

### AgentScope
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `agent_id` | UUID FK → Agent | |
| `allowed_operations` | JSONB | Массив разрешённых операций |
| `max_tasks` | INT | Макс. одновременных задач |
| `heartbeat_interval_sec` | INT | Интервал heartbeat (default 30) |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### AgentProjectAssignment
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `agent_id` | UUID FK → Agent | |
| `project_id` | UUID FK → Project | |
| `assigned_by` | UUID FK → User | |
| `assigned_at` | TIMESTAMPTZ | |

**Индексы:** UNIQUE(agent_id, project_id)

---

## Delivery Management

### Project
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization | |
| `name` | VARCHAR(128) | |
| `slug` | VARCHAR(64) | URL-safe |
| `description` | TEXT | |
| `status` | VARCHAR(16) | active, archived |
| `settings` | JSONB | Настройки проекта (review_policy и т.д.) |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |
| `deleted_at` | TIMESTAMPTZ NULL | Soft delete |

**Индексы:** UNIQUE(organization_id, slug)

### Component
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `project_id` | UUID FK → Project | |
| `name` | VARCHAR(128) | |
| `description` | TEXT | |
| `sort_order` | INT | Порядок отображения |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### Module
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `component_id` | UUID FK → Component | |
| `name` | VARCHAR(128) | |
| `description` | TEXT | |
| `sort_order` | INT | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### Feature
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `module_id` | UUID FK → Module | |
| `title` | VARCHAR(256) | |
| `description` | TEXT | |
| `priority` | VARCHAR(16) | low, medium, high, critical |
| `status` | VARCHAR(16) | draft, ready, in_progress, done |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### Task
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `feature_id` | UUID FK → Feature | |
| `title` | VARCHAR(256) | |
| `description` | TEXT | Описание задачи |
| `acceptance_criteria` | TEXT | Критерии приёмки |
| `state` | VARCHAR(32) | Состояние state machine |
| `priority` | VARCHAR(16) | low, medium, high, critical |
| `estimated_effort` | VARCHAR(16) | s, m, l, xl |
| `assigned_agent_id` | UUID FK → Agent NULL | |
| `review_policy` | VARCHAR(32) | human_only, agent_then_human, agent_auto_close |
| `due_date` | DATE NULL | |
| `completed_at` | TIMESTAMPTZ NULL | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Индексы:** (feature_id, state), (assigned_agent_id, state)

---

## Agent Workflow

### TaskClaim
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `agent_id` | UUID FK → Agent | |
| `status` | VARCHAR(16) | active, released, expired, completed |
| `claimed_at` | TIMESTAMPTZ | |
| `released_at` | TIMESTAMPTZ NULL | |
| `expires_at` | TIMESTAMPTZ | Автоматический expiry |

**Индексы:** UNIQUE(task_id) WHERE status='active'

### Heartbeat
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL PK | |
| `task_id` | UUID FK → Task | |
| `agent_id` | UUID FK → Agent | |
| `message` | TEXT NULL | Опциональный статус |
| `created_at` | TIMESTAMPTZ | |

**Индексы:** (task_id, created_at DESC) — для поиска последнего

### Subtask
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `title` | VARCHAR(256) | |
| `status` | VARCHAR(16) | pending, in_progress, done |
| `sort_order` | INT | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### ClarificationRequest
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `agent_id` | UUID FK → Agent | |
| `question` | TEXT | Вопрос агента |
| `answer` | TEXT NULL | Ответ владельца |
| `status` | VARCHAR(16) | open, answered, resolved, cancelled |
| `answered_by` | UUID FK → User NULL | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

---

## Quality & Evidence

### AcceptanceCriterion
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `description` | TEXT | Критерий |
| `status` | VARCHAR(16) | pending, met, not_met |
| `sort_order` | INT | |
| `created_at` | TIMESTAMPTZ | |

### DoDItem
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `project_id` | UUID FK → Project | |
| `title` | VARCHAR(256) | |
| `description` | TEXT | |
| `is_active` | BOOLEAN | |
| `sort_order` | INT | |
| `created_at` | TIMESTAMPTZ | |

### Evidence
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `agent_id` | UUID FK → Agent | |
| `evidence_type` | VARCHAR(32) | test_output, screenshot, log, file_diff, url, command_output |
| `title` | VARCHAR(256) | |
| `content` | TEXT | Содержимое (для логов, вывода) |
| `url` | TEXT NULL | Ссылка (для screenshots, urls) |
| `metadata` | JSONB | Доп. данные |
| `created_at` | TIMESTAMPTZ | |

### ReviewRound
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `round_number` | INT | Номер раунда |
| `policy` | VARCHAR(32) | Применённая политика |
| `status` | VARCHAR(16) | pending, in_progress, completed, cancelled |
| `verdict` | VARCHAR(16) NULL | approved, rejected |
| `reviewer_type` | VARCHAR(16) | human, agent |
| `reviewer_id` | UUID NULL | User или Agent |
| `summary` | TEXT NULL | |
| `started_at` | TIMESTAMPTZ | |
| `completed_at` | TIMESTAMPTZ NULL | |
| `created_at` | TIMESTAMPTZ | |

### ReviewFinding
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `review_round_id` | UUID FK → ReviewRound | |
| `severity` | VARCHAR(16) | info, warning, critical |
| `category` | VARCHAR(32) | correctness, security, performance, style, missing |
| `description` | TEXT | |
| `file_path` | TEXT NULL | Файл (если применимо) |
| `line_number` | INT NULL | Строка |
| `status` | VARCHAR(16) | open, addressed, dismissed |
| `created_at` | TIMESTAMPTZ | |

### ContextSnapshot
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `task_id` | UUID FK → Task | |
| `agent_id` | UUID FK → Agent | |
| `snapshot_type` | VARCHAR(16) | start, checkpoint, completion |
| `context_data` | JSONB | Контекст агента |
| `created_at` | TIMESTAMPTZ | |

---

## Observability

### AuditEvent
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL PK | |
| `organization_id` | UUID FK → Organization | |
| `actor_type` | VARCHAR(16) | user, agent, system |
| `actor_id` | UUID | |
| `action` | VARCHAR(64) | task.created, agent.claimed... |
| `entity_type` | VARCHAR(32) | task, project, agent... |
| `entity_id` | UUID | |
| `metadata` | JSONB | Доп. данные |
| `ip_address` | INET NULL | |
| `created_at` | TIMESTAMPTZ | |

**Индексы:** (organization_id, created_at DESC), (entity_type, entity_id)

---

## Notifications

### Notification
| Поле | Тип | Описание |
|------|-----|----------|
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

**Индексы:** (recipient_id, status, created_at DESC)

---

## Reporting

### Report
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization | |
| `project_id` | UUID FK → Project NULL | |
| `report_type` | VARCHAR(32) | project_summary, agent_activity, delivery_status |
| `format` | VARCHAR(8) | json, pdf, csv |
| `parameters` | JSONB | Параметры генерации |
| `file_path` | TEXT NULL | Путь к файлу |
| `status` | VARCHAR(16) | generating, ready, failed |
| `generated_by` | UUID | User или system |
| `created_at` | TIMESTAMPTZ | |
| `expires_at` | TIMESTAMPTZ NULL | |

---

## Git Integration

### GitProvider
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `organization_id` | UUID FK → Organization | |
| `provider_type` | VARCHAR(16) | gitlab, github, gitea |
| `base_url` | TEXT | URL инстанса |
| `access_token_encrypted` | TEXT | Зашифрованный токен |
| `webhook_secret_encrypted` | TEXT | Зашифрованный webhook secret |
| `is_active` | BOOLEAN | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### GitBranch
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `git_provider_id` | UUID FK → GitProvider | |
| `project_id` | UUID FK → Project | |
| `repository` | VARCHAR(256) | owner/repo |
| `branch_name` | VARCHAR(128) | |
| `last_synced_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |

**Индексы:** UNIQUE(git_provider_id, repository, branch_name)

### GitCommit
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `git_branch_id` | UUID FK → GitBranch | |
| `sha` | VARCHAR(40) | Git commit SHA |
| `message` | TEXT | |
| `author_name` | VARCHAR(128) | |
| `author_email` | VARCHAR(256) | |
| `committed_at` | TIMESTAMPTZ | |
| `synced_at` | TIMESTAMPTZ | |

**Индексы:** UNIQUE(git_branch_id, sha)

### GitLink
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `git_commit_id` | UUID FK → GitCommit | |
| `entity_type` | VARCHAR(16) | task, feature |
| `entity_id` | UUID | |
| `created_at` | TIMESTAMPTZ | |

**Индексы:** (entity_type, entity_id)

---

## ER-связи (основные)

```
Organization 1──* User (через Membership)
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
Agent *──* Project (через AgentProjectAssignment)
GitProvider 1──* GitBranch 1──* GitCommit 1──* GitLink
```
