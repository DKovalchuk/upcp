# Agent Playbook

Полное руководство для ИИ-агентов, работающих с UPCP.

## 1. Аутентификация

Все запросы требуют заголовок `X-Agent-Token`:

```
X-Agent-Token: upcp_agt_<token>
```

Токен выдаётся при регистрации агента и привязан к scope. Токен нельзя восстановить — только перевыпустить.

### Проверка подключения

```json
// MCP: whoami
{}
```

Ожидаемый ответ: объект с `agent_id`, `name`, `scopes[]`, `assignments[]`.

---

## 2. Получение контекста

### 2.1 Context Pack

Запросите контекст-пакет перед работой над задачей:

```json
// MCP: get_context_pack
{ "project_id": "...", "tier": "standard" }
```

Tiers: `minimal` | `standard` | `deep` | `debug`. См. [context-packs.md](./context-packs.md).

### 2.2 Agent Inbox

Проверяйте входящие запросы на уточнение:

```json
// MCP: get_agent_inbox
{ "status": "open" }
```

### 2.3 Capabilities

Узнайте доступные операции:

```json
// MCP: get_capabilities
{}
```

---

## 3. Жизненный цикл задачи

```
backlog → ready → claimed → in_progress → in_review → done
                                    ↘ blocked
                                    ↘ failed
```

### 3.1 Claim (захват)

```json
// MCP: claim_task
{ "task_id": "...", "idempotency_key": "<uuid-v4>" }
```

**Правила:**
- Задача должна быть в статусе `ready` или `backlog`.
- Один агент — один активный claim.
- Claim истекает через TTL (30 мин без heartbeat).
- Повторный claim тем же агентом — идемпотентная операция.

### 3.2 Heartbeat

Отправляйте heartbeat каждые 30–60 секунд:

```json
// MCP: heartbeat_task
{ "task_id": "...", "message": "анализ кодовой базы" }
```

Без heartbeat claim истекает. Задача возвращается в пул.

### 3.3 Progress

Фиксируйте прогресс:

```json
// MCP: report_progress
{ "task_id": "...", "summary": "написаны unit-тесты", "progress_percent": 40 }
```

### 3.4 Release (освобождение)

Если задача не может быть завершена:

```json
// MCP: release_task
{ "task_id": "...", "reason": "требуется уточнение по API контракту" }
```

---

## 4. Clarification (уточнения)

Когда информации недостаточно:

```json
// MCP: request_clarification
{
  "task_id": "...",
  "question": "Какой формат ожидается для due_date — ISO 8601 или Unix timestamp?",
  "blocking": true
}
```

- `blocking: true` — задача в `blocked`, агент ждёт ответа.
- `blocking: false` — задача продолжается, ответ асинхронный.

Проверка ответов: `get_agent_inbox { "status": "answered" }`.

---

## 5. Evidence (доказательства)

### Прикрепление

```json
// MCP: attach_evidence
{
  "task_id": "...",
  "evidence_type": "test_output",
  "content": "pytest: 47 passed in 3.2s"
}
```

### Типы evidence

| Тип | Описание | Пример |
|-----|----------|--------|
| `test_output` | Вывод тестов | `pytest: 47 passed` |
| `screenshot` | Скриншот UI | URL или base64 |
| `log` | Лог-файл | Фрагмент лога |
| `url` | Ссылка на ресурс | PR URL, deploy URL |
| `file` | Файл-артефакт | Путь к файлу |

---

## 6. Submit for Review

После выполнения всех AC и DoD:

```json
// MCP: submit_task_for_review
{ "task_id": "...", "summary": "CRUD реализован, тесты зелёные." }
```

**Требования:** Все DoD `passed`, нет blocking clarifications, хотя бы один evidence.

---

## 7. Review Flow

Reviewer-агент создаёт findings:

```json
// MCP: create_review_finding
{
  "review_round_id": "...",
  "severity": "medium",
  "category": "code_quality",
  "description": "Missing error handling in create()",
  "file_path": "backend/app/users/service.py",
  "line_range": "42-58"
}
```

Вердикт:

```json
// MCP: submit_review_verdict
{ "review_round_id": "...", "verdict": "needs_changes", "summary": "..." }
```

По умолчанию вердикт агента — рекомендация. Финальное решение за человеком.

---

## 8. Обработка ошибок

| Код | HTTP | Действие |
|-----|------|----------|
| `UNAUTHENTICATED` | 401 | Проверьте токен |
| `FORBIDDEN` | 403 | Проверьте scope |
| `TASK_ALREADY_CLAIMED` | 409 | Выберите другую задачу |
| `TASK_CLAIM_EXPIRED` | 410 | Повторите claim |
| `TASK_NOT_CLAIMABLE` | 422 | Проверьте статус задачи |
| `EVIDENCE_REQUIRED` | 422 | Прикрепите evidence |
| `DOD_NOT_SATISFIED` | 422 | Выполните DoD items |
| `CLARIFICATION_BLOCKING` | 422 | Дождитесь ответа |
| `RATE_LIMITED` | 429 | Exponential backoff |

---

## 9. Работа с секретами

**Запрещено:** запрашивать секреты, включать ключи/пароли в evidence, логировать секреты.

**Разрешено:** использовать env vars от runtime, ссылаться на secret provider.

Секреты автоматически редачатся LLM-шлюзом.

---

## 10. Что НЕЛЬЗЯ делать

1. Захватывать задачу без чтения context pack.
2. Игнорировать heartbeat.
3. Помечать done без evidence.
4. Делать cross-context SQL-запросы.
5. Создавать несколько claims на одну задачу.
6. Ревьюить свои задачи (self-review запрещён).
7. Хранить секреты в evidence/heartbeat/clarification.
8. Retry без backoff.

## 11. Восстановление после сбоя

1. `whoami` — токен активен?
2. `get_agent_inbox` — незавершённые задачи?
3. `task_get` для последней задачи — статус?
4. Если claim истёк — повторите `claim_task`.
5. Если `blocked` — проверьте clarification ответы.
6. Отправьте `heartbeat` для подтверждения.

## 12. Best Practices

- Context pack **до** начала работы.
- Heartbeat каждые 30–60 секунд.
- Progress при достижении milestone.
- Evidence по мере готовности.
- `blocking: true` для критических уточнений.
- Inbox при каждом запуске.
