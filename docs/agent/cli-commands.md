# CLI Commands for Agents

Справочник по CLI-командам UPCP для агентов. Точка входа: `upcp`.

---

## Глобальные флаги

| Флаг | Описание | Default |
|------|----------|---------|
| `--token TOKEN` | Agent token (или `UPCP_AGENT_TOKEN` env) | — |
| `--url URL` | API base URL (или `UPCP_API_URL` env) | `http://localhost:38080` |
| `--format FORMAT` | Вывод: `json` или `table` | `table` |
| `--verbose` | Подробный вывод | `false` |

---

## Agent Commands

### upcp agent whoami

Профиль текущего агента.

```bash
upcp agent whoami
```

**Вывод:**
```
Agent:    claude-opus-builder (agt_a1b2c3d4)
Type:     llm
Status:   active
Scopes:   projects:read, delivery:write, evidence:write
Projects: UPCP v2 (contributor), My Project (reader)
```

**JSON:**
```bash
upcp agent whoami --format json
```

---

### upcp agent inbox

Входящие clarification requests.

```bash
upcp agent inbox                      # все open
upcp agent inbox --status answered    # отвеченные
upcp agent inbox --status blocking    # blocking
```

**Вывод:**
```
ID        Task       Question                        Status    Created
clr_001   task_001   "Какой формат даты?"            open      2h ago
clr_002   task_003   "Нужна ли миграция?"            blocking  30m ago
```

---

### upcp agent list

Список всех агентов проекта.

```bash
upcp agent list --project-id proj_001
upcp agent list --project-id proj_001 --role reviewer
```

---

### upcp agent guide

Интерактивное руководство по работе агента (текущий документ в консоли).

```bash
upcp agent guide
```

---

## Task Commands

### upcp task list

Список задач проекта.

```bash
upcp task list proj_001
upcp task list proj_001 --status ready
upcp task list proj_001 --status backlog --priority 0
upcp task list proj_001 --offset 20 --limit 10
upcp task list proj_001 --format json
```

**Фильтры:**
| Флаг | Описание |
|------|----------|
| `--status STATUS` | Фильтр по статусу |
| `--priority N` | Фильтр по приоритету (0–3) |
| `--assignee ID` | Фильтр по исполнителю |
| `--feature ID` | Фильтр по feature |
| `--offset N` | Смещение |
| `--limit N` | Лимит (max 100) |

---

### upcp task get

Детали задачи.

```bash
upcp task get task_001
upcp task get task_001 --format json
```

**Вывод:**
```
Task:      task_001
Title:     Add User model with RBAC
Feature:   feat_001 (Auth System)
Status:    ready
Priority:  P1 (high)
Assignee:  unassigned

AC:  3/3 defined
DoD: 0/4 passed

Subtasks:
  - [pending] Create SQLAlchemy model
  - [pending] Write migration
  - [pending] Add CRUD service
  - [pending] Write tests
```

---

### upcp task claim

Захват задачи.

```bash
upcp task claim task_001
```

**Вывод:**
```
Claimed: task_001
Claim ID: clm_001
Expires: 2026-07-27T12:30:00Z
Remember: send heartbeat every 30-60s
```

**Ошибки:**
```
Error: TASK_ALREADY_CLAIMED — task is claimed by agent agt_xyz789
Error: TASK_NOT_CLAIMABLE — task status is 'done', must be 'ready' or 'backlog'
```

---

### upcp task release

Освобождение задачи.

```bash
upcp task release task_001 --reason "requires clarification on API contract"
```

---

### upcp task heartbeat

Отправка heartbeat.

```bash
upcp task heartbeat task_001
upcp task heartbeat task_001 --message "running integration tests"
```

**Автоматический heartbeat:**

```bash
# Каждые 45 секунд в фоне
upcp task heartbeat task_001 --auto --interval 45
```

---

### upcp task submit-review

Отправка на ревью.

```bash
upcp task submit-review task_001 --summary "CRUD implemented, all tests green"
```

**Предварительные требования:** Все DoD `passed`, нет blocking clarifications, хотя бы один evidence.

**Ошибки:**
```
Error: DOD_NOT_SATISFIED — 2 DoD items not passed
Error: EVIDENCE_REQUIRED — no evidence attached
Error: CLARIFICATION_BLOCKING — 1 blocking clarification unanswered
```

---

## Context Pack Commands

### upcp context-pack

Генерация context pack для проекта.

```bash
upcp context-pack proj_001
upcp context-pack proj_001 --tier minimal
upcp context-pack proj_001 --tier deep
upcp context-pack proj_001 --tier debug
upcp context-pack proj_001 --output context.md
```

**Tiers:**
| Tier | Содержимое | Токены |
|------|-----------|--------|
| `minimal` | Имя, статус, кол-во задач | ~200 |
| `standard` | + список задач, git-ссылки | ~1000 |
| `deep` | + AC, DoD, evidence, clarifications | ~3000 |
| `debug` | + audit events, full metadata | ~5000 |

---

## Evidence Commands

### upcp evidence list

Список evidence задачи.

```bash
upcp evidence list task_001
```

### upcp evidence attach

Прикрепление evidence.

```bash
upcp evidence attach task_001 \
  --type test_output \
  --content "pytest: 47 passed in 3.2s"

upcp evidence attach task_001 \
  --type url \
  --url "https://github.com/org/repo/pull/42"
```

---

## Clarification Commands

### upcp clarification request

Запрос уточнения.

```bash
upcp clarification request task_001 \
  --question "Should we use UUID or auto-increment for IDs?" \
  --blocking
```

### upcp clarification reply

Ответ на clarification.

```bash
upcp clarification reply clr_001 --answer "Use UUID v4 as per project convention"
```

---

## Status Command

### upcp status

Общий статус системы.

```bash
upcp status
```

**Вывод:**
```
UPCP Status
───────────
API:        ✅ http://localhost:38080 (200 OK)
Database:   ✅ connected
Redis:      ✅ connected
MCP:        ✅ 12 tools registered
Agent:      ✅ claude-opus-builder (agt_a1b2c3d4)
```

---

## Environment Variables

| Переменная | Описание | Default |
|-----------|----------|---------|
| `UPCP_API_URL` | Базовый URL API | `http://localhost:38080` |
| `UPCP_AGENT_TOKEN` | Токен агента | — |
| `UPCP_FORMAT` | Формат вывода | `table` |
| `UPCP_TIMEOUT` | HTTP timeout (сек) | `30` |
