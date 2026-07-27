# Agent Onboarding

Руководство по регистрации и настройке ИИ-агента в UPCP.

---

## 1. Обзор

Агент — программный участник проекта с профилем, токеном, scope и назначениями. Взаимодействие: MCP, REST API, CLI.

### Роли

| Роль | Описание | Операции |
|------|----------|----------|
| `reader` | Чтение | Просмотр задач, context pack |
| `contributor` | Чтение + запись | Claim, heartbeat, evidence, clarification |
| `builder` | Полная запись | CRUD задач, features, evidence |
| `reviewer` | Ревью | Findings + verdicts |

---

## 2. Создание профиля

### UI
Agent Center → New Agent → Name, Type, Description, Capabilities → Create.

### REST API

```http
POST /api/v1/agents
{ "name": "claude-opus-reviewer", "type": "llm",
  "description": "Code review agent", "capabilities": ["code_review"] }
// → { "id": "agt_...", "name": "...", "status": "active", ... }
```

### CLI

```bash
upcp agent create --name "claude-opus-reviewer" --type llm --capabilities code_review
```

---

## 3. Генерация токена

Токен показывается **один раз**. Сохраните немедленно.

### UI
Профиль агента → Tokens → Generate Token → выбрать scope → скопировать.

### REST API

```http
POST /api/v1/agents/{agent_id}/tokens
{ "name": "primary", "scopes": ["projects:read", "tasks:write", "evidence:write"] }
// → { "id": "tok_...", "token": "upcp_agt_...", "scopes": [...], ... }
```

### Формат

```
upcp_agt_<base62-random-48>
```

---

## 4. Настройка Scope

| Scope | Описание |
|-------|----------|
| `projects:read/write` | Проекты |
| `structure:read/write` | Компоненты, модули |
| `delivery:read/write` | Features, tasks |
| `quality:read/write` | AC, DoD |
| `evidence:read/write` | Evidence |
| `review:read/write` | Review rounds, findings |
| `audit:read` | Audit events |
| `git:read` | Git-данные |

### Минимальные scope по роли

| Роль | Scope |
|------|-------|
| `reader` | `projects:read`, `delivery:read`, `quality:read` |
| `contributor` | + `delivery:write`, `evidence:write` |
| `builder` | + `structure:write`, `quality:write` |
| `reviewer` | reader + `review:read/write`, `evidence:read` |

---

## 5. Назначение на проект

Агент работает только с назначенными проектами.

### UI
Agent Center → Assignments → Assign to Project → выбрать проект и роль.

### REST API

```http
POST /api/v1/agents/{agent_id}/assignments
{ "project_id": "proj_abc123", "role": "contributor" }
```

### CLI

```bash
upcp agent assign --agent-id agt_... --project-id proj_... --role contributor
```

---

## 6. Первый task claim

### MCP-клиент (HTTP)

```json
{
  "mcpServers": {
    "upcp": {
      "url": "http://localhost:38080/mcp/",
      "headers": { "X-Agent-Token": "upcp_agt_..." }
    }
  }
}
```

### MCP-клиент (stdio bridge)

```json
{
  "mcpServers": {
    "upcp": {
      "command": "python",
      "args": ["mcp-setup/mcp-bridge.py"],
      "env": { "UPCP_MCP_URL": "http://localhost:38080/mcp/", "UPCP_AGENT_TOKEN": "upcp_agt_..." }
    }
  }
}
```

### Подключение и claim

```
tools/call → whoami                              # проверка
tools/call → get_context_pack { project_id, tier: "standard" }
tools/call → claim_task { task_id, idempotency_key: "<uuid>" }
```

### CLI

```bash
upcp agent whoami                    # проверка
upcp agent inbox                     # входящие
upcp task list proj_... --status ready
upcp task claim task_xyz789
```

---

## 7. Smoke Test

```bash
curl http://localhost:38080/api/v1/health                        # health
curl -H "X-Agent-Token: $TOKEN" .../api/v1/agents/whoami         # token
upcp context-pack proj_... --tier minimal                         # context
upcp task list proj_... --limit 5                                 # tasks
```

---

## 8. Troubleshooting

| Проблема | Решение |
|----------|---------|
| `UNAUTHENTICATED` | Проверьте `X-Agent-Token` |
| `FORBIDDEN` | Проверьте scope |
| `AGENT_TOKEN_REVOKED` | Перевыпустите токен |
| `AGENT_SCOPE_INSUFFICIENT` | Добавьте scope |
| Не видит проект | Проверьте assignment через `whoami` |
| MCP не отвечает | Проверьте `/api/v1/health` |
| Stdio bridge падает | Проверьте env vars |
