# UPCP — Universal Project Control Plane (MCP)

Используй этот скилл, когда агенту нужно работать с проектами, фичами и задачами через UPCP MCP-сервер.

## Что такое UPCP

UPCP — это система управления проектами для AI-агентов. Предоставляет:

- **Проекты** — контейнеры для работы (название, описание, статус)
- **Фичи** — крупные блоки работы внутри проекта
- **Задачи** — конкретные единицы работы внутри фичи
- **Context Pack** — markdown-резюме проекта для передачи в контекст

## Архитектура

```
MCP Client (stdio) ──> mcp-bridge.py ──> UPCP FastAPI (/mcp) ──> PostgreSQL
```

UPCP exposes HTTP JSON-RPC 2.0. MCP-клиенты работают через stdio. Скрипт `mcp-bridge.py` является мостом между ними.

## Условия подключения

1. UPCP запущен (Docker: `docker compose --env-file .env.stage up -d` или локально)
2. Доступен по `http://upcp.local:3070` (или кастомный URL из `.env.*`)
3. MCP-клиент настроен с `mcp-bridge.py`

## Настройка MCP-клиента

Добавить в конфиг MCP-клиента (Qwen Code — `~/.qwen/settings.json`, Claude — `~/.claude/claude_desktop_config.json`, Cursor — `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "upcp": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp-bridge.py"]
    }
  }
}
```

Если UPCP на другом хосте/порту:

```json
{
  "mcpServers": {
    "upcp": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp-bridge.py", "--upcp-url", "http://HOST:PORT/mcp/"]
    }
  }
}
```

Альтернатива — через переменную окружения `UPCP_MCP_URL`.

## Инструменты (12)

### Чтение (6)

| Инструмент | Описание | Обязательные | Опциональные |
|---|---|---|---|
| `project_list` | Список проектов | — | `offset`, `limit` |
| `project_get` | Проект по ID | `project_id` | — |
| `feature_list` | Фичи проекта | `project_id` | `offset`, `limit` |
| `feature_get` | Фича по ID | `feature_id` | — |
| `task_list` | Задачи проекта | `project_id` | `offset`, `limit` |
| `task_get` | Задача по ID | `task_id` | — |

### Запись (6)

| Инструмент | Описание | Обязательные | Опциональные |
|---|---|---|---|
| `project_create` | Создать проект | `name` | `slug`, `description`, `status` |
| `project_update` | Обновить проект | `project_id` | `name`, `slug`, `description`, `status` |
| `feature_create` | Создать фичу | `project_id`, `name` | `slug`, `description`, `status` |
| `feature_update` | Обновить фичу | `feature_id` | `name`, `slug`, `description`, `status` |
| `task_create` | Создать задачу | `feature_id`, `title` | `description`, `status`, `priority` |
| `task_update` | Обновить задачу | `task_id` | `title`, `description`, `status`, `priority` |

### Ресурсы (1)

| URI | Описание | Параметр |
|---|---|---|
| `context_pack://project` | Markdown-резюме проекта для AI-агента | `project_id` |

## Пагинация

Все list-инструменты поддерживают пагинацию:
- `offset` — смещение (по умолчанию 0)
- `limit` — количество (по умолчанию 20, максимум 100)
- Ответ: `{items, total, offset, limit}`

## Статусы

| Сущность | Допустимые значения |
|---|---|
| Проект | `active`, `archived`, `paused` |
| Фича | `backlog`, `in_progress`, `review`, `done` |
| Задача | `backlog`, `in_progress`, `review`, `done` |

## Связи между сущностями

```
Project (1) ──> (N) Feature (1) ──> (N) Task
```

- Проект содержит фичи
- Фича содержит задачи
- Задачи создаются внутри фичи (не в проекте напрямую)

## Типичные рабочие процессы

### Посмотреть текущее состояние проекта

1. `project_list` — найти проект
2. `feature_list` — посмотреть фичи
3. `task_list` — посмотреть задачи

Или одним вызовом:
- `resources/read` с URI `context_pack://project` и `project_id` — получить markdown-резюме

### Создать новую работу

1. `project_create` — создать проект (если нет)
2. `feature_create` — создать фичу в проекте
3. `task_create` — создать задачи в фиче

### Обновить статус задачи

1. `task_update` с `task_id` и новым `status`

### Найти задачи в статусе "in_progress"

1. `task_list` с `project_id` — получить все задачи
2. Отфильтровать по `status` в ответе (серверная фильтрация пока не реализована)

## Приоритет задач

`priority` — целое число. Чем выше, тем важнее. По умолчанию 0.

## Context Pack

Вызов `resources/read` с `uri=context_pack://project` и `project_id` возвращает markdown:
- Название и статус проекта
- Список всех задач с статусами и приоритетами
- Git-ссылки (если подключены)

Используй для передачи контекста проекта в промпт.

## Ограничения

- Нет аутентификации — все эндпоинты публичны
- Нет серверной фильтрации по статусу (только клиентская)
- Пагинация: максимум 100 элементов за запрос
- Нет удаления (delete) сущностей
- Нет bulk-операций
- Context Pack — только один проект за раз

## Проверка подключения

```bash
# Health check
curl -s http://upcp.local:3070/mcp/

# Через bridge
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 mcp-bridge.py

# Список инструментов
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 mcp-bridge.py
```
