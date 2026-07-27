# Observability — UPCP v2

## Обзор

UPCP использует полный стек observability: трассировки, метрики и логи через OpenTelemetry SDK с экспортом в Grafana, Loki, Tempo и Prometheus.

---

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    UPCP Application                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  OpenTelemetry│  │  structlog   │  │  Prometheus  │  │
│  │  SDK (traces) │  │  (logs)      │  │  (metrics)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                  │           │
└─────────┼─────────────────┼──────────────────┼───────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌──────────────────────────────────────────────────────────┐
│              OpenTelemetry Collector                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ receivers │  │processors│  │exporters │              │
│  │ otlp     │→│ batch    │→│ otlp     │              │
│  │          │  │ filter   │  │ prometheus│              │
│  └──────────┘  └──────────┘  └──────────┘              │
└──────────────────────────────────────────────────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
    ┌──────────┐    ┌──────────┐    ┌──────────────────┐
    │  Tempo   │    │  Loki    │    │   Prometheus     │
    │(traces)  │    │  (logs)  │    │   (metrics)      │
    └──────────┘    └──────────┘    └──────────────────┘
          │                 │                  │
          └─────────────────┼──────────────────┘
                            ▼
                    ┌──────────────┐
                    │   Grafana    │
                    │  (дашборды)  │
                    └──────────────┘
```

---

## Structured Logging

### Формат

Все логи — structured JSON через `structlog`.

### Required Fields

```json
{
    "timestamp": "2025-07-27T10:00:00.123456Z",
    "level": "info",
    "logger": "upcp.api.routes.tasks",
    "event": "task_created",
    "request_id": "req-01934b2a-...",
    "trace_id": "abc123def456",
    "span_id": "789ghi012",
    "user_id": "01934b1f-...",
    "agent_id": null,
    "organization_id": "01934b1e-...",
    "entity_type": "task",
    "entity_id": "01934b35-...",
    "duration_ms": 42,
    "status_code": 201
}
```

### Поля (обязательные)

| Поле | Тип | Описание |
|------|-----|----------|
| `timestamp` | ISO 8601 | UTC, микросекунды |
| `level` | string | debug, info, warning, error, critical |
| `logger` | string | Модуль-источник |
| `event` | string | Название события (snake_case) |
| `request_id` | string | UUID запроса (из middleware) |
| `trace_id` | string | OpenTelemetry trace ID |
| `span_id` | string | OpenTelemetry span ID |

### Поля (контекстные, если применимо)

| Поле | Тип | Описание |
|------|-----|----------|
| `user_id` | UUID | ID пользователя |
| `agent_id` | UUID | ID агента |
| `organization_id` | UUID | ID организации |
| `entity_type` | string | Тип сущности |
| `entity_id` | UUID | ID сущности |
| `duration_ms` | int | Длительность операции |
| `status_code` | int | HTTP статус код |
| `error_code` | string | Код ошибки |
| `http_method` | string | HTTP метод |
| `http_path` | string | HTTP путь |

### Уровни логирования

| Уровень | Использование |
|---------|--------------|
| `debug` | Отладочная информация, SQL-запросы |
| `info` | Штатные операции (создание, обновление) |
| `warning` | Деградация, retry, fallback |
| `error` | Ошибки обработки, нештатные ситуации |
| `critical` | Фатальные ошибки, потеря данных |

### Redaction

Поля, которые НИКОГДА не логируются:

- `password`, `password_hash`
- `token`, `token_hash`, `access_token`, `refresh_token`
- `secret`, `api_key`, `encryption_key`
- Тело HTTP-запросов к `/auth/*`

---

## Metrics

### HTTP Metrics

| Метрика | Тип | Labels | Описание |
|---------|-----|--------|----------|
| `http_requests_total` | counter | method, path, status | Всего запросов |
| `http_request_duration_seconds` | histogram | method, path, status | Длительность запросов |
| `http_request_size_bytes` | histogram | method, path | Размер запроса |
| `http_response_size_bytes` | histogram | method, path | Размер ответа |
| `http_requests_in_flight` | gauge | — | Текущие запросы |

### Database Metrics

| Метрика | Тип | Labels | Описание |
|---------|-----|--------|----------|
| `db_query_duration_seconds` | histogram | operation, table | Длительность запросов |
| `db_connections_active` | gauge | — | Активные соединения |
| `db_connections_idle` | gauge | — | Простаивающие соединения |
| `db_query_errors_total` | counter | operation, table, error_type | Ошибки БД |

### Redis Metrics

| Метрика | Тип | Labels | Описание |
|---------|-----|--------|----------|
| `redis_command_duration_seconds` | histogram | command | Длительность команд |
| `redis_connections_active` | gauge | — | Активные соединения |
| `redis_cache_hits_total` | counter | cache_key_prefix | Попадания в кэш |
| `redis_cache_misses_total` | counter | cache_key_prefix | Промахи кэша |

### Business Metrics

| Метрика | Тип | Labels | Описание |
|---------|-----|--------|----------|
| `tasks_created_total` | counter | project_id, priority | Создано задач |
| `tasks_completed_total` | counter | project_id, priority | Завершено задач |
| `task_cycle_time_seconds` | histogram | priority | Время от claim до done |
| `claims_active` | gauge | project_id | Активные claims |
| `claims_expired_total` | counter | project_id | Истёкшие claims |
| `heartbeats_received_total` | counter | agent_id, project_id | Получено heartbeat |
| `reviews_completed_total` | counter | verdict, reviewer_type | Завершённые ревью |
| `review_duration_seconds` | histogram | reviewer_type | Длительность ревью |
| `agents_active` | gauge | project_id | Активные агенты |
| `clarifications_open` | gauge | project_id | Открытые clarification |

---

## Traces

### Instrumentation

#### HTTP (FastAPI)

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

FastAPIInstrumentor.instrument_app(app)
```

- Один span на запрос
- Attributes: `http.method`, `http.url`, `http.status_code`, `http.request_id`

#### Database (SQLAlchemy)

```python
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

SQLAlchemyInstrumentor().instrument(engine=engine)
```

- Один span на SQL-запрос
- Attributes: `db.system`, `db.statement`, `db.name`

#### Redis

```python
from opentelemetry.instrumentation.redis import RedisInstrumentor

RedisInstrumentor().instrument()
```

- Один span на Redis-команду
- Attributes: `db.system`, `db.statement`

#### Custom Spans

```python
from opentelemetry import trace

tracer = trace.get_tracer("upcp.agent_workflow")

async def claim_task(task_id, agent_id):
    with tracer.start_as_current_span("claim_task") as span:
        span.set_attribute("task.id", str(task_id))
        span.set_attribute("agent.id", str(agent_id))
        # ...
        span.set_attribute("claim.result", "success")
```

### MCP Tool Spans

Каждый MCP tool call — отдельный span:

```
Span: mcp.tool.claim_task
  Attributes:
    mcp.tool.name: claim_task
    mcp.tool.input.task_id: 01934b35-...
    mcp.tool.result: success
  Child Spans:
    - db.query (SELECT task)
    - db.query (INSERT claim)
    - db.query (UPDATE task)
    - redis.set (heartbeat key)
```

### Git Integration Spans

```
Span: git.sync_commits
  Attributes:
    git.provider: gitlab
    git.repository: owner/repo
    git.branch: main
    git.commits_synced: 5
  Child Spans:
    - http.request (GitLab API)
    - db.query (INSERT commits)
```

---

## Dashboards

### 1. Service Health

| Panel | Тип | Источник |
|-------|-----|----------|
| Request rate (RPS) | Graph | `rate(http_requests_total[5m])` |
| Error rate | Graph | `rate(http_requests_total{status=~"5.."}[5m])` |
| Latency p50/p95/p99 | Graph | `histogram_quantile(0.95, http_request_duration_seconds)` |
| Active connections | Stat | `http_requests_in_flight` |
| DB connections | Stat | `db_connections_active` |
| Redis connections | Stat | `redis_connections_active` |
| Uptime | Stat | `up` |

### 2. Auth & Security

| Panel | Тип | Источник |
|-------|-----|----------|
| Auth failures | Graph | `rate(http_requests_total{status="401"}[5m])` |
| Permission denied | Graph | `rate(http_requests_total{status="403"}[5m])` |
| Rate limited | Graph | `rate(http_requests_total{status="429"}[5m])` |
| Active sessions | Stat | Логи |
| Login attempts | Graph | Логи (event=auth.*) |

### 3. Agent Activity

| Panel | Тип | Источник |
|-------|-----|----------|
| Active agents | Stat | `agents_active` |
| Active claims | Gauge | `claims_active` |
| Heartbeat rate | Graph | `rate(heartbeats_received_total[5m])` |
| Claim expiry rate | Graph | `rate(claims_expired_total[5m])` |
| Task cycle time | Heatmap | `task_cycle_time_seconds` |
| Agent throughput | Graph | `rate(tasks_completed_total[1h])` |

### 4. Delivery & Quality

| Panel | Тип | Источник |
|-------|-----|----------|
| Tasks by state | Pie | `tasks_created_total` - `tasks_completed_total` |
| Completion rate | Graph | `rate(tasks_completed_total[1d])` |
| Review turnaround | Graph | `review_duration_seconds` |
| Review verdicts | Pie | `reviews_completed_total by verdict` |
| Open clarifications | Stat | `clarifications_open` |
| Evidence per task | Histogram | Логи |

---

## Alerts (Prometheus AlertManager)

| Alert | Condition | Severity |
|-------|-----------|----------|
| High error rate | `rate(http_requests_total{status=~"5.."}[5m]) > 0.05` | critical |
| High latency | `histogram_quantile(0.99, http_request_duration_seconds) > 2` | warning |
| DB connection pool full | `db_connections_active > 0.9 * max` | warning |
| Redis down | `redis_up == 0` | critical |
| No heartbeats | `rate(heartbeats_received_total[10m]) == 0 AND claims_active > 0` | warning |
| Claim expiry spike | `rate(claims_expired_total[5m]) > 0.1` | warning |
| Review backlog | `reviews_completed_total{status="pending"} > 10` | warning |
