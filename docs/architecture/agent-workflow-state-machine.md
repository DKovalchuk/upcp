# Agent Workflow State Machines — UPCP v2

## Обзор

UPCP использует конечные автоматы для управления жизненным циклом задач, claims, clarification requests и review rounds. Все переходы строго определены и логируются в audit trail.

---

## 1. Task State Machine

### Диаграмма

```
                        ┌──────────────┐
                        │   backlog    │
                        └──────┬───────┘
                               │ set_ready
                               ▼
                        ┌──────────────┐
                   ┌───▶│    ready     │◀─────────────────────────┐
                   │    └──────┬───────┘                          │
                   │           │ claim_task                        │
                   │           ▼                                   │
                   │    ┌──────────────┐                          │
                   │    │   claimed    │                          │
                   │    └──────┬───────┘                          │
                   │           │ start_work                        │
                   │           ▼                                   │
                   │    ┌──────────────┐                          │
                   │    │ in_progress  │◀────────────┐            │
                   │    └──┬───┬───┬───┘            │            │
                   │       │   │   │                │            │
       release_task│       │   │   │ request_       │            │
                   │       │   │   │ clarification   │            │
                   │       │   │   ▼                │            │
                   │       │   │ ┌──────────────────┴──┐         │
                   │       │   │ │needs_clarification   │         │
                   │       │   │ └──────────┬───────────┘         │
                   │       │   │            │ clarify_resolved    │
                   │       │   │            └─────────────────────┘
                   │       │   │                                    │
                   │       │   │ block                              │
                   │       │   ▼                                    │
                   │       │ ┌──────────────┐                      │
                   │       │ │   blocked    │──────────────────────┘
                   │       │ └──────┬───────┘      unblock
                   │       │        │ block_resolved
                   │       │        └──▶ in_progress
                   │       │
                   │       │ submit_for_review
                   │       ▼
                   │ ┌───────────────────┐
                   │ │  ready_for_review  │
                   │ └───────┬───────────┘
                   │         │
                   │    ┌────┴────┐
                   │    │         │
                   │    ▼         ▼
                   │ ┌──────┐ ┌──────────────────┐
                   │ │ done │ │changes_requested  │
                   │ └──────┘ └────────┬──────────┘
                   │                   │ rework
                   │                   └──▶ in_progress
                   │
                   │ cancel
                   ▼
              ┌──────────┐
              │ cancelled │
              └──────────┘
```

### Состояния

| Состояние | Описание | Допустимые переходы |
|-----------|----------|---------------------|
| `backlog` | Задача создана, не готова к работе | → `ready` |
| `ready` | Готова к claim агентом | → `claimed`, → `cancelled` |
| `claimed` | Заclaimлена агентом, ещё не начата | → `in_progress`, → `ready` (release) |
| `in_progress` | Агент работает | → `blocked`, → `needs_clarification`, → `ready_for_review`, → `ready` (release) |
| `blocked` | Заблокирована внешним фактором | → `in_progress` (unblock) |
| `needs_clarification` | Ожидает ответа от владельца | → `in_progress` (resolved), → `cancelled` |
| `ready_for_review` | Отправлена на ревью | → `done`, → `changes_requested` |
| `changes_requested` | Ревью потребовало доработок | → `in_progress` (rework) |
| `done` | Задача завершена | — (финальное) |
| `cancelled` | Отменена | — (финальное) |

### Правила переходов

1. **backlog → ready**: Только owner или admin
2. **ready → claimed**: Атомарная операция, только через `claim_task`
3. **claimed → in_progress**: Агент вызывает `start_work` (через первый heartbeat)
4. **in_progress → ready**: Агент отпускает задачу (release)
5. **in_progress → blocked**: Агент указывает причину блокировки
6. **in_progress → needs_clarification**: Агент отправляет clarification request
7. **in_progress → ready_for_review**: Агент подтверждает выполнение
8. **ready_for_review → done**: Ревью approved
9. **ready_for_review → changes_requested**: Ревью rejected
10. **changes_requested → in_progress**: Агент приступает к доработке
11. **Любое → cancelled**: Только owner/admin, кроме `done`

---

## 2. TaskClaim State Machine

### Диаграмма

```
          ┌──────────┐
          │  active   │
          └──┬──┬──┬──┘
             │  │  │
    release  │  │  │ task_completed
             │  │  │
             ▼  │  ▼
     ┌────────┐ │ ┌───────────┐
     │released│ │ │ completed  │
     └────────┘ │ └───────────┘
                │
         heartbeat_timeout
                │
                ▼
         ┌──────────┐
         │  expired  │
         └──────────┘
```

### Состояния

| Состояние | Описание | Триггер |
|-----------|----------|---------|
| `active` | Claim активен | `claim_task` |
| `released` | Агент добровольно отпустил | `release_task` |
| `expired` | Heartbeat timeout | Автоматически |
| `completed` | Задача завершена | `submit_for_review` → approved |

### Heartbeat Timeout

- Default: 120 секунд без heartbeat → claim expired
- Конфигурируется per-project (`heartbeat_timeout_sec`)
- Expired claim освобождает задачу → состояние `ready`
- Audit event: `claim.expired`

---

## 3. ClarificationRequest State Machine

### Диаграмма

```
          ┌──────────┐
          │   open    │
          └──┬────┬───┘
             │    │
     answer  │    │ cancel
             ▼    ▼
     ┌──────────┐ ┌───────────┐
     │ answered │ │ cancelled  │
     └────┬─────┘ └───────────┘
          │
     resolve
          │
          ▼
     ┌──────────┐
     │ resolved  │
     └──────────┘
```

### Состояния

| Состояние | Описание | Триггер |
|-----------|----------|---------|
| `open` | Вопрос задан, ожидает ответа | `request_clarification` |
| `answered` | Владелец ответил | `answer_clarification` |
| `resolved` | Агент подтвердил получение ответа | Агент вызывает `resolve_clarification` |
| `cancelled` | Отменён (владельцем или если задача отменена) | `cancel_clarification` |

### Правила

1. Clarification request приостанавливает задачу (`in_progress` → `needs_clarification`)
2. Ответ владельца возвращает задачу в `in_progress` (автоматически)
3. Если задача отменяется — все open clarification requests → `cancelled`
4. Агент может отменить свой own clarification request

---

## 4. ReviewRound State Machine

### Диаграмма

```
          ┌───────────┐
          │  pending   │
          └─────┬──────┘
                │ start_review
                ▼
          ┌───────────┐
          │in_progress │
          └──┬─────┬──┘
             │     │
    approve  │     │ reject
             ▼     ▼
     ┌──────────┐ ┌──────────┐
     │ completed │ │ completed │
     │ (approved)│ │ (rejected)│
     └──────────┘ └──────────┘

    (Любое не-fинальное → cancelled)
```

### Состояния

| Состояние | Описание | Триггер |
|-----------|----------|---------|
| `pending` | Ревью создано, ожидает ревьюера | `submit_task_for_review` |
| `in_progress` | Ревьюер приступил | `start_review` |
| `completed` | Ревью завершено с вердиктом | `submit_review_verdict` |
| `cancelled` | Ревью отменено | `cancel_review` |

### Verdicts

| Вердикт | Действие | Следующее состояние задачи |
|---------|----------|---------------------------|
| `approved` | Задача считается done | `done` |
| `rejected` | Задача возвращается на доработку | `changes_requested` |

### Правила

1. Review round создаётся автоматически при `submit_task_for_review`
2. Ревьюер определяется политикой проекта
3. Agent-ревьюер может review только если политика = `agent_review_then_human` или `agent_auto_close_if_allowed`
4. При `agent_auto_close_if_allowed`: агент может approve без human review (если задача low/medium priority)
5. При `agent_review_then_human`: после agent review требуется human confirmation
6. Human может в любой момент переопределить вердикт агента
7. Новый review round создаётся при rework (changes_requested → in_progress → ready_for_review)

---

## Audit Trail

Каждый переход state machine записывает audit event:

```json
{
    "action": "task.state_changed",
    "entity_type": "task",
    "entity_id": "01934b35-...",
    "metadata": {
        "from_state": "in_progress",
        "to_state": "ready_for_review",
        "trigger": "submit_for_review",
        "actor_type": "agent",
        "actor_id": "01934b2a-..."
    }
}
```

---

## Timeout и Auto-Recovery

| Ситуация | Timeout | Действие |
|----------|---------|----------|
| Heartbeat отсутствует | 120 сек | Claim expired → задача в `ready` |
| Clarification без ответа | 7 дней | Notification → owner |
| Review pending | 3 дня | Notification → reviewer |
| Task in progress | 14 дней | Notification → owner (configurable) |

---

## Реализация

State machine реализована в `agent_workflow` bounded context:

```
src/upcp/contexts/agent_workflow/
├── state_machine.py          # Определение переходов
├── transitions.py            # Guards и actions
├── services/
│   ├── claim_service.py      # Claim/release/expiry
│   ├── heartbeat_service.py  # Heartbeat recording
│   ├── clarification_service.py
│   └── review_service.py
└── models/
    ├── task_claim.py
    ├── heartbeat.py
    ├── clarification.py
    └── review_round.py
```
