# Agent Workflow — Спецификация

> Связано: [UPCP v2 PRD](./upcp-v2.md) §3.2 | Milestone: M9

## 1. Обзор

Agent Workflow определяет жизненный цикл задачи от момента создания до завершения, с акцентом на подотчётность AI-агентов и контроль со стороны людей.

## 2. Жизненный цикл задачи

```
open → claimed → in_progress → in_review → done
  │       │           │            │
  │       │           │            └→ changes_requested → in_progress
  │       │           │
  │       │           └→ blocked → in_progress (clarification resolved)
  │       │
  │       └→ open (release/timeout)
  │
  └→ cancelled
```

### 2.1 Статусы

| Статус | Описание | Владелец |
|--------|----------|----------|
| `open` | Задача создана, ожидает назначения | — |
| `claimed` | Агент взял задачу (claim) | agent |
| `in_progress` | Агент работает | agent |
| `blocked` | Ожидание уточнений | agent / human |
| `in_review` | Результат на проверке | reviewer |
| `changes_requested` | Рецензент запросил изменения | reviewer |
| `done` | Задача завершена | — |
| `cancelled` | Задача отменена | human |

### 2.2 Переходы

| Из | В | Кто | Условие |
|----|---|-----|---------|
| open | claimed | agent | `POST /tasks/{id}/claim` |
| claimed | in_progress | agent | `PATCH /tasks/{id}` status=working |
| in_progress | blocked | agent | `POST /tasks/{id}/clarification-request` |
| blocked | in_progress | human | `POST /tasks/{id}/clarification/{id}/resolve` |
| in_progress | in_review | agent | `POST /tasks/{id}/submit-review` + evidence attached |
| in_review | done | reviewer | `POST /tasks/{id}/approve` |
| in_review | changes_requested | reviewer | `POST /tasks/{id}/request-changes` |
| changes_requested | in_progress | agent | agent resumes work |
| claimed | open | system | heartbeat timeout (7 мин) |
| any (≠done, ≠cancelled) | cancelled | human (admin/owner) | `POST /tasks/{id}/cancel` |

## 3. Claim (Захват задачи)

### API
```
POST /api/v1/tasks/{task_id}/claim
Authorization: ApiKey <agent-key>
```

### Правила
- Задача должна быть в статусе `open`
- Только `agent` роль может claim
- Один агент — одна активная claim (опционально, через `max_active_claims` в проекте)
- Claim атомарен (row-level lock)

### Release
```
POST /api/v1/tasks/{task_id}/release
```
- Агент может release задачу добровольно
- Система автоматически release при heartbeat timeout

## 4. Heartbeat

### Механизм
```
POST /api/v1/tasks/{task_id}/heartbeat
Authorization: ApiKey <agent-key>
Body: { "message": "Running integration tests...", "progress": 60 }
```

### Таймауты

| Параметр | Значение | Описание |
|----------|----------|----------|
| `heartbeat_interval` | 30-60 сек | Рекомендуемый интервал |
| `heartbeat_stale` | 7 мин | Задача считается abandoned |
| `heartbeat_dead` | 15 мин | Автоматический release + уведомление |

### Поведение при stale
1. **7 мин без heartbeat** → задача помечается `stale`, уведомление владельцу проекта
2. **15 мин без heartbeat** → автоматический release, задача возвращается в `open`
3. Audit event: `task.stale_detected`, `task.auto_released`

## 5. Clarification Flow

Когда агенту нужна дополнительная информация:

```
POST /api/v1/tasks/{task_id}/clarification-request
Body: {
  "question": "Какой формат ответа ожидается: JSON или CSV?",
  "context": "В спецификации оба варианта упоминаются"
}
```

### Поведение
- Задача переходит в `blocked`
- Clarification создаётся как child entity задачи
- Уведомление ответственному человеку
- Heartbeat暂停 (stale timer暂停 пока задача blocked)

### Ответ
```
POST /api/v1/tasks/{task_id}/clarifications/{id}/resolve
Body: { "answer": "JSON, с полем metadata для расширений" }
```

## 6. Agent Inbox

Каждый агент имеет inbox для получения сообщений:

### Структура
```python
class InboxMessage:
    id: str
    agent_id: str
    task_id: str | None
    from_type: Literal["human", "agent", "system"]
    from_id: str
    subject: str
    body: str
    priority: Literal["low", "normal", "high", "urgent"]
    read: bool
    created_at: datetime
```

### API
```
GET  /api/v1/agents/{agent_id}/inbox?unread=true
POST /api/v1/agents/{agent_id}/inbox/{id}/read
POST /api/v1/agents/{agent_id}/inbox/send
```

### Использование
- Система: уведомления о stale, release, changes_requested
- Человек: команды, контекст, обратная связь
- Другие агенты: запросы на collaboration

## 7. Agent Playbook

Каждый проект может иметь playbook — набор инструкций для агентов.

### Структура
```yaml
# playbook.yaml
version: "1"
agent_instructions: |
  Используй pytest для тестов. Запускай `make test` перед submit.
  Минимальный coverage: 80%.
quality_gates:
  - name: lint
    command: "make lint"
    required: true
  - name: test
    command: "make test"
    required: true
  - name: typecheck
    command: "make typecheck"
    required: false
evidence_requirements:
  - type: test_result
    description: "Output of pytest with coverage"
  - type: diff
    description: "Git diff of changes"
```

### API
```
GET  /api/v1/projects/{id}/playbook
PUT  /api/v1/projects/{id}/playbook
```

## 8. MCP Interface

Агенты взаимодействуют через MCP (Model Context Protocol):

| MCP Tool | Аналог REST | Описание |
|----------|-------------|----------|
| `claim_task` | `POST /tasks/{id}/claim` | Захватить задачу |
| `heartbeat` | `POST /tasks/{id}/heartbeat` | Отправить heartbeat |
| `report_progress` | `PATCH /tasks/{id}` | Обновить прогресс |
| `report_completion` | `POST /tasks/{id}/submit-review` | Завершить работу |
| `report_blockage` | `POST /tasks/{id}/clarification-request` | Запросить уточнение |
| `read_playbook` | `GET /projects/{id}/playbook` | Прочитать инструкции |
| `get_inbox` | `GET /agents/{id}/inbox` | Проверить входящие |

## 9. CLI Interface

```bash
upcp task list --project my-project --status open
upcp task claim <task-id>
upcp task heartbeat <task-id> --message "Working on tests"
upcp task submit <task-id> --evidence test_result:pytest.xml
```

## 10. Ограничения

- Максимум 10 активных claims на агента (настраивается на уровне проекта)
- Heartbeat payload не более 1KB
- Clarification message не более 4KB
- Inbox хранит сообщения 30 дней, затем archive
- Playbook не более 64KB
