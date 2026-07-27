# Аудит-события — UPCP v2

> Область: `security` / `audit` | Версия: 2.0.0

## 1. Обзор

Все значимые действия в UPCP записываются в неизменяемый аудит-лог.
Аудит-события используются для расследования инцидентов, compliance и мониторинга.

## 2. Формат события

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

### 2.1 Обязательные поля

| Поле          | Описание                                  |
|--------------|------------------------------------------|
| `id`         | UUID события                              |
| `timestamp`  | ISO 8601, UTC                            |
| `event_type` | Иерархическое имя (dot-separated)        |
| `severity`   | `info`, `warning`, `critical`            |
| `actor`      | Кто совершил действие                    |
| `resource`   | Над чем совершено действие               |

### 2.2 Severity Levels

| Уровень    | Описание                                        |
|-----------|------------------------------------------------|
| `info`    | Штатные операции                                |
| `warning` | Подозрительные, но допустимые операции          |
| `critical`| Нарушения безопасности, блокировки              |

## 3. События аутентификации

| Event Type                        | Severity  | Описание                              |
|----------------------------------|-----------|---------------------------------------|
| `auth.login.success`             | info      | Успешный вход                        |
| `auth.login.failed`              | warning   | Неудачная попытка входа              |
| `auth.login.blocked`             | critical  | Вход заблокирован (brute-force)      |
| `auth.logout`                    | info      | Выход из системы                     |
| `auth.token.refresh`             | info      | Обновление access token              |
| `auth.token.created`             | info      | Создание нового refresh token        |
| `auth.token.revoked`             | info      | Отзыв токена                         |
| `auth.token.reuse_detected`      | critical  | Обнаружен повторный отзыванный token |
| `auth.password.changed`          | info      | Смена пароля                         |
| `auth.password.reset_requested`  | info      | Запрос сброса пароля                 |
| `auth.password.reset_completed`  | info      | Пароль сброшен                       |
| `auth.account.locked`            | warning   | Аккаунт заблокирован                 |
| `auth.account.unlocked`          | info      | Аккаунт разблокирован                |
| `auth.account.deactivated`       | warning   | Аккаунт деактивирован                |
| `auth.account.activated`         | info      | Аккаунт активирован                  |
| `auth.setup.completed`           | info      | First-run setup завершён             |

### 3.1 Детали для auth событий

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

## 4. События агентов

| Event Type                        | Severity  | Описание                              |
|----------------------------------|-----------|---------------------------------------|
| `agent.token.created`            | info      | Создан токен агента                  |
| `agent.token.revoked`            | info      | Отозван токен агента                 |
| `agent.token.rotated`            | info      | Ротация токена агента                |
| `agent.token.expired`            | info      | Токен агента истёк                   |
| `agent.task.claimed`             | info      | Агент захватил задачу                |
| `agent.task.released`            | info      | Агент освободил задачу               |
| `agent.task.submitted`           | info      | Агент отправил результат             |
| `agent.task.approved`            | info      | Результат одобрен                    |
| `agent.task.rejected`            | info      | Результат отклонён                   |
| `agent.task.timeout`             | warning   | Таймаут выполнения задачи            |
| `agent.heartbeat`                | info      | Heartbeat от агента                  |
| `agent.heartbeat.stale`          | warning   | Агент не отвечает (>7 мин)           |
| `agent.clarification.requested`  | info      | Агент запросил уточнение             |
| `agent.clarification.provided`   | info      | Уточнение предоставлено              |
| `agent.evidence.submitted`       | info      | Агент загрузил доказательство        |
| `agent.review.requested`         | info      | Запрошен review                      |
| `agent.review.completed`         | info      | Review завершён                      |
| `agent.file.created`             | info      | Агент создал файл                    |
| `agent.file.modified`            | info      | Агент изменил файл                   |
| `agent.mcp.tool_called`          | info      | Вызов MCP инструмента                |
| `agent.mcp.tool_denied`          | warning   | MCP инструмент заблокирован          |
| `agent.scope.denied`             | warning   | Попытка доступа за рамками scope     |
| `agent.rate_limit.exceeded`      | warning   | Превышен rate limit                  |

### 4.1 Детали для agent событий

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

## 5. События администрирования

| Event Type                              | Severity  | Описание                          |
|----------------------------------------|-----------|-----------------------------------|
| `admin.role.assigned`                  | warning   | Назначена роль                    |
| `admin.role.revoked`                   | warning   | Отозвана роль                     |
| `admin.user.created`                   | info      | Создан пользователь               |
| `admin.user.deactivated`               | warning   | Деактивирован пользователь        |
| `admin.user.activated`                 | info      | Активирован пользователь          |
| `admin.project.created`                | info      | Создан проект                     |
| `admin.project.deleted`                | critical  | Удалён проект                     |
| `admin.project.settings.changed`       | warning   | Изменены настройки проекта        |
| `admin.organization.created`           | info      | Создана организация               |
| `admin.organization.deleted`           | critical  | Удалена организация               |
| `admin.organization.settings.changed`  | warning   | Изменены настройки организации    |
| `admin.integration.added`              | warning   | Добавлена интеграция              |
| `admin.integration.removed`            | warning   | Удалена интеграция                |
| `admin.secret.rotated`                 | warning   | Ротирован секрет                  |
| `admin.backup.created`                 | info      | Создан backup                     |
| `admin.backup.restored`                | critical  | Восстановлен из backup            |

## 6. Системные события

| Event Type                        | Severity  | Описание                              |
|----------------------------------|-----------|---------------------------------------|
| `system.startup`                  | info      | Приложение запущено                   |
| `system.shutdown`                 | info      | Приложение остановлено                |
| `system.config.changed`           | warning   | Изменена конфигурация                 |
| `system.error.unhandled`          | critical  | Необработанная ошибка                 |
| `system.rate_limit.abuse`         | critical  | Обнаружено злоупотребление            |
| `system.ip.blocked`               | critical  | IP заблокирован                       |

## 7. Хранение и ротация

### 7.1 Хранение

- Основное: PostgreSQL таблица `audit_events`
- Партиционирование: по месяцам (`audit_events_2026_07`)
- Индексы: `timestamp`, `event_type`, `actor.id`, `resource.id`

### 7.2 Ротация

- Active partition: текущий месяц + следующий
- Retention: 12 месяцев в горячем хранилище
- Архив: сжатые партиции в object storage (S3/MinIO)
- Удаление: по запросу владельца (GDPR compliance)

### 7.3 Неизменяемость

- Audit events — append-only (нет UPDATE/DELETE)
- Права на запись: только audit service account
- Права на чтение: Admin, Owner
- Integrity: хеш-цепочка (каждое событие включает хеш предыдущего)

## 8. Запрос аудит-лога

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

- Пагинация: cursor-based
- Фильтры: event_type, actor_id, resource_id, severity, date range
- Экспорт: CSV, JSON (до 10,000 записей за запрос)
