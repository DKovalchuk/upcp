# mcp-setup

Файлы для подключения AI-агентов к UPCP через MCP.

## Содержимое

| Файл | Назначение |
|---|---|
| `mcp-bridge.py` | Stdio↔HTTP мост для MCP-клиентов |
| `AGENT_PROMPT.md` | Промпт для любого AI-агента (копируй и вставляй) |
| `SKILL.md` | Скилл для Qwen Code (референс по инструментам и паттернам) |

## Быстрый старт

### 1. Убедиться, что UPCP запущен

```bash
docker compose -f docker-compose.stage.yml up -d
curl -s http://upcp.local:3070/mcp/
```

### 2. Проверить мост

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 mcp-setup/mcp-bridge.py
```

### 3. Настроить MCP-клиент

Добавить в `~/.qwen/settings.json` (или аналог):

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

### 4. Дать агенту промпт

Скопируй содержимое `AGENT_PROMPT.md` и вставь в чат с AI-агентом.

## UPCP на другом хосте

```bash
python3 mcp-setup/mcp-bridge.py --upcp-url http://your-host:3070/mcp/
```

Или через переменную окружения:

```bash
UPCP_MCP_URL=http://your-host:3070/mcp/ python3 mcp-setup/mcp-bridge.py
```

## Debug

```bash
UPCP_MCP_DEBUG=1 python3 mcp-setup/mcp-bridge.py
```

Логи пишутся в stderr и не мешают JSON-RPC на stdout.
