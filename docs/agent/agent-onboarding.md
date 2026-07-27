# Agent Onboarding

Руководство по регистрации и настройке ИИ-агента в UPCP.

---

## 1. Обзор

Агент в UPCP — это программный участник проекта с собственным профилем, токеном, scope и набором назначений. Агент взаимодействует с платформой через MCP (Model Context Protocol), REST API или CLI.

### Роли агентов

| Роль | Описание | Типичные операции |
|------|----------|-------------------|
| `reader` | Только чтение | Просмотр задач, context pack |
| `contributor` | Чтение + evidence | Claim, heartbeat, evidence, clarification |
| `builder` | Полная запись | CRUD задач, features, evidence |
| `reviewer` | Ревью | Чтение + findings + verdicts |

---

## 2. Создание профиля агента

### 2.1 Через UI

1. Откройте **Agent Center** → **New Agent**.
2. Заполните поля:
   - **Name** — уникальное имя (например, `claude-opus-reviewer`).
   - **Type** — тип агента (`llm`, `script`, `human_assisted`).
   - **Description** — назначение агента.
   - **Capabilities** — список поддерживаемых операций.
3. Нажмите **Create**.

### 2.2 Через REST API

```http
POST /api/v1/agents
Content-Type: application/json

{
  "name": "claude-opus-reviewer",
  "type": "llm",
  "description": "Code review agent based on Claude Opus",
  "capabilities": ["code_review", "security_audit"]
}
```

Ответ:

```json
{
  "id": "agt_a1b2c3d4",
  "name": "claude-opus-reviewer",
  "type": "llm",
  "status": "active",
  "created_at": "2026-07-27T12:00:00Z"
}
```

### 2.3 Через CLI

```bash
upcp agent create \
  --name "claude-opus-reviewer" \
  --type llm \
  --description "Code review agent" \
  --capabilities code_review,security_audit
```

---

## 3. Генерация токена

Токен показывается **один раз** при создании. Сохраните его немедленно.

### 3.1 Через UI

1. Откройте профиль агента → вкладка **Tokens**.
2. Нажмите **Generate Token**.
3. Выберите scope (см. раздел 4).
4. Скопируйте токен.

### 3.2 Через REST API

```http
POST /api/v1/agents/{agent_id}/tokens
Content-Type: application/json

{
  "name": "primary",
  "scopes": ["projects:read", "tasks:write", "evidence:write"]
}
```

Ответ:

```json
{
  "id": "tok_x1y2z3",
  "token": "upcp_agt_a1b2c3d4e5f6...",
  "name": "primary",
  "scopes": ["projects:read", "tasks:write", "evidence:write"],
  "created_at": "2026-07-27T12:00:00Z",
  "expires_at": null
}
```

### 3.3 Формат токена

```
upcp_agt_<base62-random-48>
```

Префикс `upcp_agt_` позволяет идентифицировать тип credentials.

---

## 4. Настройка Scope

Scope определяет, какие операции агент может выполнять.

### 4.1 Доступные scopes

| Scope | Описание |
|-------|----------|
| `projects:read` | Просмотр проектов |
| `projects:write` | Создание/редактирование проектов |
| `structure:read` | Просмотр компонентов, модулей |
| `structure:write` | CRUD компонентов, модулей |
| `delivery:read` | Просмотр features, tasks |
| `delivery:write` | CRUD features, tasks |
| `quality:read` | Просмотр AC, DoD |
| `quality:write` | CRUD AC, DoD |
| `evidence:read` | Просмотр evidence |
| `evidence:write` | Прикрепление evidence |
| `review:read` | Просмотр review rounds |
| `review:write` | Создание findings, verdicts |
| `audit:read` | Просмотр audit events |
| `git:read` | Просмотр git-данных |

### 4.2 Минимальные scope по роли

| Роль | Минимальные scope |
|------|-------------------|
| `reader` | `projects:read`, `delivery:read`, `quality:read` |
| `contributor` | reader + `delivery:write`, `evidence:write` |
| `builder` | contributor + `structure:write`, `quality:write` |
| `reviewer` | reader + `review:read`, `review:write`, `evidence:read` |

---

## 5. Назначение на проект

Агент работает только с назначенными проектами.

### 5.1 Через UI

1. Откройте **Agent Center** → профиль агента → вкладка **Assignments**.
2. Нажмите **Assign to Project**.
3. Выберите проект и роль.

### 5.2 Через REST API

```http
POST /api/v1/agents/{agent_id}/assignments
Content-Type: application/json

{
  "project_id": "proj_abc123",
  "role": "contributor"
}
```

### 5.3 Через CLI

```bash
upcp agent assign \
  --agent-id agt_a1b2c3d4 \
  --project-id proj_abc123 \
  --role contributor
```

---

## 6. Первый task claim

### 6.1 Подключение через MCP

Настройте MCP-клиент (Claude Desktop, Qwen Code, Cursor и т.д.):

```json
{
  "mcpServers": {
    "upcp": {
      "url": "http://localhost:38080/mcp/",
      "headers": {
        "X-Agent-Token": "upcp_agt_a1b2c3d4e5f6..."
      }
    }
  }
}
```

Для stdio-клиентов используйте bridge:

```json
{
  "mcpServers": {
    "upcp": {
      "command": "python",
      "args": ["mcp-setup/mcp-bridge.py"],
      "env": {
        "UPCP_MCP_URL": "http://localhost:38080/mcp/",
        "UPCP_AGENT_TOKEN": "upcp_agt_a1b2c3d4e5f6..."
      }
    }
  }
}
```

### 6.2 Проверка подключения

```
tools/call → whoami
```

Ожидаемый ответ:

```json
{
  "agent_id": "agt_a1b2c3d4",
  "name": "claude-opus-reviewer",
  "scopes": ["projects:read", "tasks:write", "evidence:write"],
  "assignments": [
    { "project_id": "proj_abc123", "project_name": "UPCP v2", "role": "contributor" }
  ]
}
```

### 6.3 Захват задачи

```
tools/call → get_context_pack
  project_id: "proj_abc123"
  tier: "standard"

tools/call → claim_task
  task_id: "task_xyz789"
  idempotency_key: "<uuid-v4>"
```

### 6.4 Проверка через CLI

```bash
# Проверить подключение
upcp agent whoami

# Посмотреть inbox
upcp agent inbox

# Список задач проекта
upcp task list proj_abc123 --status ready
```

---

## 7. Тестирование connectivity

### 7.1 Smoke Test

```bash
# 1. Проверить health
curl http://localhost:38080/api/v1/health

# 2. Проверить токен
curl -H "X-Agent-Token: $TOKEN" http://localhost:38080/api/v1/agents/whoami

# 3. Получить context pack
upcp context-pack proj_abc123 --tier minimal

# 4. Список задач
upcp task list proj_abc123 --limit 5
```

### 7.2 MCP Connectivity Test

```
# initialize
{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}

# tools/list
{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}

# whoami
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"whoami","arguments":{}},"id":3}
```

---

## 8. Troubleshooting

| Проблема | Решение |
|----------|---------|
| `UNAUTHENTICATED` | Проверьте заголовок `X-Agent-Token` |
| `FORBIDDEN` | Проверьте scope токена |
| `AGENT_TOKEN_REVOKED` | Перевыпустите токен |
| `AGENT_SCOPE_INSUFFICIENT` | Добавьте нужный scope |
| Не видит проект | Проверьте assignment через `whoami` |
| MCP не отвечает | Проверьте `http://localhost:38080/api/v1/health` |
| Stdio bridge падает | Проверьте `UPCP_MCP_URL` и `UPCP_AGENT_TOKEN` env vars |
