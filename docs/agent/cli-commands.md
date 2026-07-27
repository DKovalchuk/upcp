# CLI Commands for Agents

Справочник по CLI-командам UPCP для агентов. Точка входа: `upcp`.

---

## Глобальные флаги

| Флаг | Описание | Default |
|------|----------|---------|
| `--token TOKEN` | Agent token (или `UPCP_AGENT_TOKEN` env) | — |
| `--url URL` | API base URL (или `UPCP_API_URL` env) | `http://localhost:38080` |
| `--format FORMAT` | `json` или `table` | `table` |
| `--verbose` | Подробный вывод | `false` |

---

## Agent Commands

### upcp agent whoami

Профиль текущего агента.

```bash
upcp agent whoami
# Agent: claude-opus-builder (agt_a1b2c3d4)
# Type: llm · Status: active
# Scopes: projects:read, delivery:write, evidence:write
# Projects: UPCP v2 (contributor)
```

### upcp agent inbox

Входящие clarification requests.

```bash
upcp agent inbox                      # open
upcp agent inbox --status answered    # отвеченные
upcp agent inbox --status blocking    # blocking
# ID        Task       Question                        Status    Created
# clr_001   task_001   "Какой формат даты?"            open      2h ago
```

### upcp agent list

Агенты проекта.

```bash
upcp agent list --project-id proj_001
upcp agent list --project-id proj_001 --role reviewer
```

### upcp agent guide

Руководство в консоли.

```bash
upcp agent guide
```

---

## Task Commands

### upcp task list

```bash
upcp task list proj_001
upcp task list proj_001 --status ready
upcp task list proj_001 --priority 0 --limit 10
upcp task list proj_001 --format json
```

**Фильтры:** `--status`, `--priority`, `--assignee`, `--feature`, `--offset`, `--limit`.

### upcp task get

```bash
upcp task get task_001
# Task: task_001
# Title: Add User model with RBAC
# Status: ready · Priority: P1 · Assignee: unassigned
# AC: 3/3 defined · DoD: 0/4 passed
```

### upcp task claim

```bash
upcp task claim task_001
# Claimed: task_001 · Claim ID: clm_001
# Expires: 2026-07-27T12:30:00Z
# Remember: send heartbeat every 30-60s
```

Ошибки: `TASK_ALREADY_CLAIMED`, `TASK_NOT_CLAIMABLE`.

### upcp task release

```bash
upcp task release task_001 --reason "requires clarification on API contract"
```

### upcp task heartbeat

```bash
upcp task heartbeat task_001
upcp task heartbeat task_001 --message "running integration tests"
upcp task heartbeat task_001 --auto --interval 45   # авто в фоне
```

### upcp task submit-review

```bash
upcp task submit-review task_001 --summary "CRUD implemented, all tests green"
```

Требования: DoD `passed`, нет blocking clarifications, хотя бы один evidence.
Ошибки: `DOD_NOT_SATISFIED`, `EVIDENCE_REQUIRED`, `CLARIFICATION_BLOCKING`.

---

## Context Pack Commands

### upcp context-pack

```bash
upcp context-pack proj_001                       # standard
upcp context-pack proj_001 --tier minimal         # минимальный
upcp context-pack proj_001 --tier deep            # глубокий
upcp context-pack proj_001 --tier debug           # полный
upcp context-pack proj_001 --output context.md    # в файл
```

| Tier | Содержимое | Токены |
|------|-----------|--------|
| `minimal` | Имя, статус, кол-во задач | ~200 |
| `standard` | + задачи, git-ссылки | ~1000 |
| `deep` | + AC, DoD, evidence | ~3000 |
| `debug` | + audit, metadata | ~5000 |

---

## Evidence Commands

```bash
upcp evidence list task_001
upcp evidence attach task_001 --type test_output --content "pytest: 47 passed"
upcp evidence attach task_001 --type url --url "https://github.com/.../pull/42"
```

---

## Clarification Commands

```bash
upcp clarification request task_001 --question "UUID or auto-increment?" --blocking
upcp clarification reply clr_001 --answer "Use UUID v4 as per project convention"
```

---

## Status Command

```bash
upcp status
# API:        ✅ http://localhost:38080 (200 OK)
# Database:   ✅ connected
# Redis:      ✅ connected
# MCP:        ✅ 12 tools registered
# Agent:      ✅ claude-opus-builder (agt_a1b2c3d4)
```

---

## Environment Variables

| Переменная | Описание | Default |
|-----------|----------|---------|
| `UPCP_API_URL` | Базовый URL | `http://localhost:38080` |
| `UPCP_AGENT_TOKEN` | Токен агента | — |
| `UPCP_FORMAT` | Формат вывода | `table` |
| `UPCP_TIMEOUT` | HTTP timeout (сек) | `30` |
