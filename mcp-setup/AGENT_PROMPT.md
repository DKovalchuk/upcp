# Промпт для AI-агента: подключение к UPCP через MCP

Скопируй этот промпт целиком и вставь в любой AI-агент (Qwen Code, Claude, Cursor, Windsurf и т.д.).
Агент выполнит настройку и сможет управлять проектами через UPCP.

---

## Промпт (начало)

```
# Задача: подключиться к UPCP и управлять проектами через MCP

## Что такое UPCP

UPCP (Universal Project Control Plane) — это система управления проектами,
спроектированная для AI-агентов. Через неё ты можешь:

- Создавать и управлять проектами
- Разбивать работу на фичи и задачи
- Отслеживать статус выполнения
- Получать контекст проекта в формате markdown

UPCP работает как сервер, к которому ты подключаешься через MCP.

## Архитектура

Твой MCP-клиент (stdio) → mcp-bridge.py (мост) → UPCP (HTTP JSON-RPC 2.0)

## Шаг 1: Установка

### 1.1 Проверить, что UPCP запущен

```bash
curl -s http://localhost:38080/mcp
```

Ожидаемый ответ: `{"status":"ok","service":"mcp-server"}`

Если UPCP не запущен, его нужно поднять:

```bash
cd /path/to/upcp
docker compose up -d
# Подождать ~15 секунд, затем повторить проверку
curl -s http://localhost:38080/health
```

### 1.2 Убедиться, что Python 3.10+ доступен

```bash
python3 --version
```

### 1.3 Создать файл mcp-bridge.py

Файл уже должен находиться в репозитории: `<upcp-root>/mcp-setup/mcp-bridge.py`

Если его нет — создай вручную (см. содержимое ниже в разделе «mcp-bridge.py»).

### 1.4 Настроить MCP-клиент

Добавь UPCP в конфиг MCP-клиента:

**Qwen Code** (`~/.qwen/settings.json`):
```json
{
  "mcpServers": {
    "upcp": {
      "command": "python3",
      "args": ["/absolute/path/to/upcp/mcp-setup/mcp-bridge.py"],
      "description": "UPCP — управление проектами"
    }
  }
}
```

**Claude Desktop** (`~/.claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "upcp": {
      "command": "python3",
      "args": ["/absolute/path/to/upcp/mcp-setup/mcp-bridge.py"]
    }
  }
}
```

**Cursor** (`.cursor/mcp.json` в проекте):
```json
{
  "mcpServers": {
    "upcp": {
      "command": "python3",
      "args": ["/absolute/path/to/upcp/mcp-setup/mcp-bridge.py"]
    }
  }
}
```

**Если UPCP на другом хосте/порту:**
```json
{
  "mcpServers": {
    "upcp": {
      "command": "python3",
      "args": [
        "/absolute/path/to/upcp/mcp-setup/mcp-bridge.py",
        "--upcp-url", "http://HOST:PORT/mcp"
      ]
    }
  }
}
```

### 1.5 Проверить подключение

После настройки вызови `tools/list` — должен вернуть 12 инструментов.
Затем вызови `project_list` — должен вернуть список проектов.

## Шаг 2: Использование

### Модель данных

```
Project (проект)
  ├── Feature 1 (фича)
  │     ├── Task 1.1 (задача)
  │     ├── Task 1.2
  │     └── Task 1.3
  ├── Feature 2
  │     ├── Task 2.1
  │     └── Task 2.2
  └── Feature 3
        └── Task 3.1
```

Проект → содержит фичи → содержит задачи.
Задачи создаются внутри фичи (не в проекте напрямую).

### Статусы

| Сущность | Допустимые значения |
|---|---|
| Проект | `active`, `archived`, `paused` |
| Фича | `backlog`, `in_progress`, `review`, `done` |
| Задача | `backlog`, `in_progress`, `review`, `done` |

### Инструменты

#### Чтение

| Инструмент | Назначение | Параметры |
|---|---|---|
| `project_list` | Все проекты | `offset`, `limit` |
| `project_get` | Проект по ID | `project_id` |
| `feature_list` | Фичи проекта | `project_id`, `offset`, `limit` |
| `feature_get` | Фича по ID | `feature_id` |
| `task_list` | Задачи проекта | `project_id`, `offset`, `limit` |
| `task_get` | Задача по ID | `task_id` |

#### Запись

| Инструмент | Назначение | Обязательные | Опциональные |
|---|---|---|---|
| `project_create` | Новый проект | `name` | `slug`, `description`, `status` |
| `project_update` | Обновить проект | `project_id` | `name`, `slug`, `description`, `status` |
| `feature_create` | Новая фича | `project_id`, `name` | `slug`, `description`, `status` |
| `feature_update` | Обновить фичу | `feature_id` | `name`, `slug`, `description`, `status` |
| `task_create` | Новая задача | `feature_id`, `title` | `description`, `status`, `priority` |
| `task_update` | Обновить задачу | `task_id` | `title`, `description`, `status`, `priority` |

#### Ресурсы

| URI | Что возвращает | Параметр |
|---|---|---|
| `context_pack://project` | Markdown-резюме проекта | `project_id` |

### Пагинация

Все list-инструменты: `offset` (по умолчанию 0), `limit` (по умолчанию 20, макс 100).
Ответ: `{items, total, offset, limit}`.

## Шаг 3: Когда использовать

### Когда использовать UPCP

UPCP подходит для управления проектами, в которых AI-агент является основным
или равноправным участником. Используй UPCP когда:

- Нужно структурировать работу: проект → фичи → задачи
- Нужно отслеживать прогресс по задачам
- Нужно передать контекст проекта другому агенту (через context pack)
- Нужно разделить работу между несколькими агентами (через задачи)

### Когда НЕ использовать UPCP

- Для управления кодом (используй git)
- Для мониторинга инфраструктуры (используй Grafana/Prometheus)
- Для одноразовых задач (просто выполни их)

### Типичные сценарии

#### Сценарий 1: Начать новый проект

```
1. project_create(name="My Project", description="...")
2. feature_create(project_id=..., name="Feature 1")
3. task_create(feature_id=..., title="Task 1")
4. task_create(feature_id=..., title="Task 2")
```

#### Сценарий 2: Посмотреть текущий статус

```
1. project_list → найти проект
2. task_list(project_id=...) → посмотреть все задачи
3. Отфильтровать по status в ответе
```

Или быстрее:
```
1. resources/read(uri="context_pack://project", project_id=...)
   → получить markdown с полным контекстом
```

#### Сценарий 3: Обновить прогресс

```
1. task_get(task_id=...) → текущее состояние
2. task_update(task_id=..., status="in_progress") → начать работу
3. task_update(task_id=..., status="done") → завершить
```

#### Сценарий 4: Разделить работу между агентами

```
1. feature_create(project_id=..., name="Agent A work")
2. task_create(feature_id=..., title="Subtask 1")
3. task_create(feature_id=..., title="Subtask 2")
4. Дать feature_id второму агенту → он работает со своими задачами
```

## mcp-bridge.py

Если файл отсутствует, создай его со следующим содержимым:

```python
#!/usr/bin/env python3
"""Stdio-HTTP bridge for UPCP MCP server.

Reads JSON-RPC 2.0 messages from stdin, forwards them to the UPCP HTTP
endpoint, and writes responses to stdout. Stderr is used for logging.

Usage:
    python3 mcp-bridge.py
    python3 mcp-bridge.py --upcp-url http://192.168.1.10:38080/mcp
    UPCP_MCP_URL=http://host:port/mcp python3 mcp-bridge.py
"""

import json
import os
import sys
import urllib.error
import urllib.request


def resolve_url() -> str:
    """Resolve UPCP MCP URL from args, env, or default."""
    for i, arg in enumerate(sys.argv):
        if arg == "--upcp-url" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return os.environ.get("UPCP_MCP_URL", "http://localhost:38080/mcp")


UPCP_URL = resolve_url()
DEBUG = os.environ.get("UPCP_MCP_DEBUG", "").lower() in ("1", "true", "yes")


def log(msg: str) -> None:
    if DEBUG:
        sys.stderr.write(f"[upcp-bridge] {msg}\n")
        sys.stderr.flush()


def send_error(req_id: object, code: int, message: str) -> None:
    resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()


def forward(request: dict) -> dict:
    """Forward a JSON-RPC request to the UPCP MCP server via HTTP POST."""
    payload = json.dumps(request).encode("utf-8")
    http_req = urllib.request.Request(
        UPCP_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    req_id = request.get("id")

    try:
        with urllib.request.urlopen(http_req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            log(f"HTTP {resp.status} for {request.get('method')}")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        log(f"HTTP {exc.code}: {err_body[:200]}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": f"HTTP {exc.code}: {err_body[:500]}"},
        }
    except urllib.error.URLError as exc:
        log(f"Connection error: {exc.reason}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": f"Cannot reach UPCP at {UPCP_URL}: {exc.reason}"},
        }
    except Exception as exc:
        log(f"Unexpected error: {exc}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32603, "message": str(exc)},
        }


def main() -> None:
    log(f"Bridge started, UPCP URL: {UPCP_URL}")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            send_error(None, -32700, "Parse error")
            continue

        log(f" <- {request.get('method', '?')} id={request.get('id', 'N/A')}")

        # Notifications (no id) get no response per JSON-RPC spec
        if "id" not in request:
            log("   (notification, skipped)")
            continue

        response = forward(request)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

    log("Bridge stdin closed")


if __name__ == "__main__":
    main()
```

## Ограничения

- Нет аутентификации (все эндпоинты публичны)
- Нет серверной фильтрации (только клиентская)
- Нет удаления сущностей
- Пагинация: макс 100 элементов за запрос
- Контекст-пак: один проект за раз

## Troubleshooting

| Проблема | Решение |
|---|---|
| `Cannot reach UPCP` | Проверить: `curl http://localhost:38080/mcp` |
| `HTTP 500` | Проверить логи контейнера: `docker compose logs app` |
| `project_id is required` | Сначала вызови `project_list`, чтобы получить ID |
| `feature_id is required` | Задачи создаются в фиче. Сначала создай фичу |
| Пустой список проектов | UPCP чистый — создай первый проект через `project_create` |
| Bridge молчит | Проверить python3 и путь к файлу. Запусти с `UPCP_MCP_DEBUG=1` |
```

## Промпт (конец)
