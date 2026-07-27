# MCP Tools — UPCP v2

## Обзор

UPCP предоставляет ИИ-агентам доступ через Model Context Protocol (MCP). Все MCP tools разделены на три категории: **read** (чтение данных), **write** (модификация) и **admin** (управление). Права доступа определяются scope агента.

---

## Аутентификация

Агенты аутентифицируются через `AgentToken`, передаваемый в MCP handshake. Токен определяет:
- Организацию агента
- Scope (разрешённые операции, проекты)
- Лимиты (max_tasks, heartbeat_interval)

---

## Read Tools

### `whoami`

Возвращает информацию о текущем агенте и его capabilities.

```
→ {}
← {
    "agent_id": "01934b2a-...",
    "name": "claude-code-agent",
    "agent_type": "claude",
    "organization_id": "01934b1f-...",
    "capabilities": ["code_review", "implementation"],
    "assigned_projects": ["01934b2c-...", "01934b2d-..."]
}
```

### `get_capabilities`

Возвращает полный список доступных операций для текущего агента.

```
→ {}
← {
    "allowed_operations": ["task.read", "task.write", "evidence.create"],
    "max_tasks": 3,
    "heartbeat_interval_sec": 30
}
```

### `get_agent_playbook`

Возвращает playbook/инструкции для агента в контексте проекта.

```
→ { "project_id": "01934b2c-..." }
← {
    "project_id": "01934b2c-...",
    "guidelines": "...",
    "conventions": "...",
    "forbidden_patterns": ["..."],
    "required_patterns": ["..."]
}
```

### `list_projects`

Список проектов, назначенных агенту.

```
→ { "offset": 0, "limit": 20 }
← {
    "data": [
        {
            "id": "01934b2c-...",
            "name": "UPCP",
            "slug": "upcp",
            "status": "active"
        }
    ],
    "meta": { "total": 2, "offset": 0, "limit": 20 }
}
```

### `get_project`

Детали проекта с настройками.

```
→ { "project_id": "01934b2c-..." }
← {
    "id": "01934b2c-...",
    "name": "UPCP",
    "description": "...",
    "settings": { "review_policy": "agent_then_human" },
    "stats": { "tasks_total": 42, "tasks_done": 18 }
}
```

### `list_components`

Компоненты проекта.

```
→ { "project_id": "01934b2c-...", "offset": 0, "limit": 50 }
← { "data": [...], "meta": {...} }
```

### `list_modules`

Модули компонента.

```
→ { "component_id": "01934b30-...", "offset": 0, "limit": 50 }
← { "data": [...], "meta": {...} }
```

### `list_features`

Фичи модуля или проекта.

```
→ {
    "project_id": "01934b2c-...",
    "module_id": null,
    "filter": { "status": "ready" },
    "offset": 0, "limit": 20
}
← { "data": [...], "meta": {...} }
```

### `list_tasks`

Задачи с фильтрацией. Основной инструмент для поиска работы.

```
→ {
    "project_id": "01934b2c-...",
    "filter": {
        "state": "ready",
        "priority": "high"
    },
    "sort": "-priority,created_at",
    "offset": 0, "limit": 20
}
← { "data": [...], "meta": {...} }
```

### `get_task`

Полная информация о задаче с relationships.

```
→ { "task_id": "01934b35-..." }
← {
    "id": "01934b35-...",
    "title": "Implement auth middleware",
    "description": "...",
    "acceptance_criteria": "...",
    "state": "in_progress",
    "priority": "high",
    "feature": { "id": "...", "title": "..." },
    "module": { "id": "...", "name": "..." },
    "component": { "id": "...", "name": "..." },
    "project": { "id": "...", "name": "..." },
    "subtasks": [...],
    "evidence_count": 3,
    "review_rounds": [...],
    "clarification_requests": [...]
}
```

### `get_context_pack`

Контекстный пакет для задачи — вся информация, необходимая агенту для работы.

```
→ { "task_id": "01934b35-..." }
← {
    "task": { ... },
    "project_guidelines": "...",
    "component_context": "...",
    "related_tasks": [...],
    "git_branch": "feature/auth-middleware",
    "recent_commits": [...]
}
```

### `get_agent_inbox`

Входящие сообщения для агента: ответы на clarification, уведомления.

```
→ { "project_id": null, "unreadOnly": true }
← {
    "data": [
        {
            "type": "clarification_answer",
            "task_id": "01934b35-...",
            "message": "...",
            "created_at": "2025-07-27T10:00:00Z"
        }
    ],
    "meta": { "total": 1 }
}
```

### `list_evidence`

Evidence для задачи.

```
→ { "task_id": "01934b35-...", "offset": 0, "limit": 20 }
← { "data": [...], "meta": {...} }
```

### `list_review_rounds`

Раунды ревью для задачи.

```
→ { "task_id": "01934b35-..." }
← {
    "data": [
        {
            "id": "...",
            "round_number": 1,
            "status": "completed",
            "verdict": "approved",
            "findings": [...]
        }
    ]
}
```

---

## Write Tools

### `create_component`

```
→ {
    "project_id": "01934b2c-...",
    "name": "Backend API",
    "description": "FastAPI application"
}
← { "data": { "id": "...", "name": "Backend API", ... } }
```

### `update_component`

```
→ {
    "component_id": "01934b30-...",
    "name": "Backend API v2",
    "description": "Updated description"
}
← { "data": { ... } }
```

### `create_module`

```
→ {
    "component_id": "01934b30-...",
    "name": "Authentication",
    "description": "Auth module"
}
← { "data": { ... } }
```

### `update_module`

```
→ { "module_id": "...", "name": "Auth & RBAC" }
← { "data": { ... } }
```

### `create_feature`

```
→ {
    "module_id": "...",
    "title": "JWT Authentication",
    "description": "...",
    "priority": "high"
}
← { "data": { ... } }
```

### `update_feature`

```
→ { "feature_id": "...", "status": "ready", "priority": "critical" }
← { "data": { ... } }
```

### `create_task`

```
→ {
    "feature_id": "...",
    "title": "Implement login endpoint",
    "description": "...",
    "acceptance_criteria": "...",
    "priority": "high",
    "estimated_effort": "m",
    "review_policy": "agent_then_human"
}
← { "data": { ... } }
```

### `update_task`

```
→ {
    "task_id": "...",
    "title": "Updated title",
    "description": "..."
}
← { "data": { ... } }
```

**Ограничения:** Нельзя менять `state` напрямую (используйте state machine tools).

### `create_subtask`

```
→ { "task_id": "...", "title": "Write unit tests" }
← { "data": { ... } }
```

### `claim_task`

Атомарный claim задачи. Если задача уже заclaimлена — ошибка.

```
→ { "task_id": "..." }
← {
    "data": {
        "claim_id": "...",
        "task_id": "...",
        "agent_id": "...",
        "claimed_at": "...",
        "expires_at": "..."
    }
}
```

**Ошибки:**
- `409 TASK_ALREADY_CLAIMED` — задача уже заclaimлена другим агентом
- `422 TASK_NOT_CLAIMABLE` — задача не в состоянии ready

### `release_task`

Освобождение задачи (агент не может продолжить).

```
→ { "task_id": "...", "reason": "Need more context" }
← { "data": { "released": true } }
```

### `heartbeat_task`

Периодический сигнал жизни. Обязателен каждые 30-60 секунд.

```
→ { "task_id": "...", "message": "Running tests..." }
← { "data": { "received_at": "..." } }
```

### `add_task_note`

Добавление заметки к задаче.

```
→ { "task_id": "...", "note": "Found edge case in auth flow..." }
← { "data": { "id": "...", "created_at": "..." } }
```

### `request_clarification`

Запрос уточнения у владельца проекта.

```
→ {
    "task_id": "...",
    "question": "Should the login endpoint support OAuth2 or only email/password?"
}
← { "data": { "clarification_id": "...", "status": "open" } }
```

### `answer_clarification`

Ответ на clarification (для owner через MCP или UI).

```
→ {
    "clarification_id": "...",
    "answer": "Only email/password for MVP. OAuth2 will be a separate task."
}
← { "data": { "status": "answered" } }
```

### `attach_evidence`

Прикрепление evidence к задаче.

```
→ {
    "task_id": "...",
    "evidence_type": "test_output",
    "title": "Unit test results",
    "content": "42 passed, 0 failed...",
    "metadata": { "test_framework": "pytest" }
}
← { "data": { "id": "...", "created_at": "..." } }
```

### `submit_task_for_review`

Отправка задачи на ревью. Меняет state на `ready_for_review`.

```
→ {
    "task_id": "...",
    "summary": "Implemented login endpoint with JWT. All tests pass."
}
← { "data": { "state": "ready_for_review", "review_round_id": "..." } }
```

### `request_agent_review`

Запрос ревью от другого агента (если политика позволяет).

```
→ {
    "task_id": "...",
    "reviewer_agent_id": "...",
    "focus": "Security review of auth implementation"
}
← { "data": { "review_round_id": "..." } }
```

### `submit_review_verdict`

Отправка вердикта ревью (для agent-ревьюеров).

```
→ {
    "review_round_id": "...",
    "verdict": "approved",
    "summary": "LGTM. Clean implementation, good test coverage.",
    "findings": [
        {
            "severity": "info",
            "category": "style",
            "description": "Consider extracting token generation to a service",
            "file_path": "src/auth/jwt.py",
            "line_number": 42
        }
    ]
}
← { "data": { "status": "completed", "verdict": "approved" } }
```

---

## Admin Tools

### `create_agent`

```
→ {
    "name": "claude-code-reviewer",
    "agent_type": "claude",
    "description": "Code review specialist",
    "capabilities": ["code_review"],
    "scope": {
        "allowed_operations": ["task.read", "review.*"],
        "max_tasks": 5
    },
    "project_ids": ["01934b2c-..."]
}
← { "data": { "id": "...", "token": "mcp_...", "token_plaintext": "..." } }
```

**Важно:** `token_plaintext` возвращается ТОЛЬКО при создании.

### `revoke_agent_token`

```
→ { "agent_id": "...", "token_id": "..." }
← { "data": { "revoked": true } }
```

### `manage_roles`

```
→ {
    "action": "assign",
    "user_id": "...",
    "project_id": "...",
    "role": "member"
}
← { "data": { "assigned": true } }
```

### `manage_project_members`

```
→ {
    "action": "add",
    "project_id": "...",
    "agent_id": "...",
    "role": "contributor"
}
← { "data": { "added": true } }
```

### `manage_settings`

```
→ {
    "project_id": "...",
    "settings": {
        "review_policy": "agent_then_human",
        "heartbeat_timeout_sec": 120,
        "auto_unclaim_after_sec": 3600
    }
}
← { "data": { "updated": true } }
```

---

## Scope и Permissions

### Операции

| Операция | Описание | Read Tools | Write Tools | Admin Tools |
|----------|----------|------------|-------------|-------------|
| `project.read` | Чтение проектов | ✅ | — | — |
| `task.read` | Чтение задач | ✅ | — | — |
| `task.write` | Создание/claim задач | ✅ | ✅ | — |
| `evidence.create` | Создание evidence | ✅ | ✅ | — |
| `review.submit` | Отправка на ревью | ✅ | ✅ | — |
| `review.review` | Проведение ревью | ✅ | ✅ | — |
| `clarification.*` | Clarification flow | ✅ | ✅ | — |
| `structure.write` | CRUD компонентов/модулей | ✅ | ✅ | — |
| `agent.manage` | Управление агентами | ✅ | ✅ | ✅ |
| `admin.*` | Администрирование | ✅ | ✅ | ✅ |

### Правила

1. Агент может работать только с назначенными проектами
2. Claim возможен только если state = `ready`
3. Heartbeat обязателен, иначе claim истекает
4. Clarification приостанавливает задачу
5. Evidence привязана к текущему claim
6. Review submit возможен только из состояния `in_progress`
