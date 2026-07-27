# Observability — UPCP v2

## Overview

UPCP uses a full observability stack: traces, metrics, and logs via the OpenTelemetry SDK with export to Grafana, Loki, Tempo, and Prometheus.

---

## Architecture

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
                    │ (dashboards) │
                    └──────────────┘
```

---

## Structured Logging

### Format

All logs are structured JSON via `structlog`.

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

### Fields (required)

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | ISO 8601 | UTC, microseconds |
| `level` | string | debug, info, warning, error, critical |
| `logger` | string | Source module |
| `event` | string | Event name (snake_case) |
| `request_id` | string | Request UUID (from middleware) |
| `trace_id` | string | OpenTelemetry trace ID |
| `span_id` | string | OpenTelemetry span ID |

### Fields (contextual, when applicable)

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | UUID | User ID |
| `agent_id` | UUID | Agent ID |
| `organization_id` | UUID | Organization ID |
| `entity_type` | string | Entity type |
| `entity_id` | UUID | Entity ID |
| `duration_ms` | int | Operation duration |
| `status_code` | int | HTTP status code |
| `error_code` | string | Error code |
| `http_method` | string | HTTP method |
| `http_path` | string | HTTP path |

### Logging Levels

| Level | Usage |
|-------|-------|
| `debug` | Debug information, SQL queries |
| `info` | Normal operations (create, update) |
| `warning` | Degradation, retry, fallback |
| `error` | Processing errors, abnormal situations |
| `critical` | Fatal errors, data loss |

### Redaction

Fields that are NEVER logged:

- `password`, `password_hash`
- `token`, `token_hash`, `access_token`, `refresh_token`
- `secret`, `api_key`, `encryption_key`
- HTTP request bodies to `/auth/*`

---

## Metrics

### HTTP Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_requests_total` | counter | method, path, status | Total requests |
| `http_request_duration_seconds` | histogram | method, path, status | Request duration |
| `http_request_size_bytes` | histogram | method, path | Request size |
| `http_response_size_bytes` | histogram | method, path | Response size |
| `http_requests_in_flight` | gauge | — | Current in-flight requests |

### Database Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `db_query_duration_seconds` | histogram | operation, table | Query duration |
| `db_connections_active` | gauge | — | Active connections |
| `db_connections_idle` | gauge | — | Idle connections |
| `db_query_errors_total` | counter | operation, table, error_type | DB errors |

### Redis Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `redis_command_duration_seconds` | histogram | command | Command duration |
| `redis_connections_active` | gauge | — | Active connections |
| `redis_cache_hits_total` | counter | cache_key_prefix | Cache hits |
| `redis_cache_misses_total` | counter | cache_key_prefix | Cache misses |

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `tasks_created_total` | counter | project_id, priority | Tasks created |
| `tasks_completed_total` | counter | project_id, priority | Tasks completed |
| `task_cycle_time_seconds` | histogram | priority | Time from claim to done |
| `claims_active` | gauge | project_id | Active claims |
| `claims_expired_total` | counter | project_id | Expired claims |
| `heartbeats_received_total` | counter | agent_id, project_id | Heartbeats received |
| `reviews_completed_total` | counter | verdict, reviewer_type | Reviews completed |
| `review_duration_seconds` | histogram | reviewer_type | Review duration |
| `agents_active` | gauge | project_id | Active agents |
| `clarifications_open` | gauge | project_id | Open clarifications |

---

## Traces

### Instrumentation

#### HTTP (FastAPI)

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

FastAPIInstrumentor.instrument_app(app)
```

- One span per request
- Attributes: `http.method`, `http.url`, `http.status_code`, `http.request_id`

#### Database (SQLAlchemy)

```python
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

SQLAlchemyInstrumentor().instrument(engine=engine)
```

- One span per SQL query
- Attributes: `db.system`, `db.statement`, `db.name`

#### Redis

```python
from opentelemetry.instrumentation.redis import RedisInstrumentor

RedisInstrumentor().instrument()
```

- One span per Redis command
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

Each MCP tool call is a separate span:

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

| Panel | Type | Source |
|-------|------|--------|
| Request rate (RPS) | Graph | `rate(http_requests_total[5m])` |
| Error rate | Graph | `rate(http_requests_total{status=~"5.."}[5m])` |
| Latency p50/p95/p99 | Graph | `histogram_quantile(0.95, http_request_duration_seconds)` |
| Active connections | Stat | `http_requests_in_flight` |
| DB connections | Stat | `db_connections_active` |
| Redis connections | Stat | `redis_connections_active` |
| Uptime | Stat | `up` |

### 2. Auth & Security

| Panel | Type | Source |
|-------|------|--------|
| Auth failures | Graph | `rate(http_requests_total{status="401"}[5m])` |
| Permission denied | Graph | `rate(http_requests_total{status="403"}[5m])` |
| Rate limited | Graph | `rate(http_requests_total{status="429"}[5m])` |
| Active sessions | Stat | Logs |
| Login attempts | Graph | Logs (event=auth.*) |

### 3. Agent Activity

| Panel | Type | Source |
|-------|------|--------|
| Active agents | Stat | `agents_active` |
| Active claims | Gauge | `claims_active` |
| Heartbeat rate | Graph | `rate(heartbeats_received_total[5m])` |
| Claim expiry rate | Graph | `rate(claims_expired_total[5m])` |
| Task cycle time | Heatmap | `task_cycle_time_seconds` |
| Agent throughput | Graph | `rate(tasks_completed_total[1h])` |

### 4. Delivery & Quality

| Panel | Type | Source |
|-------|------|--------|
| Tasks by state | Pie | `tasks_created_total` - `tasks_completed_total` |
| Completion rate | Graph | `rate(tasks_completed_total[1d])` |
| Review turnaround | Graph | `review_duration_seconds` |
| Review verdicts | Pie | `reviews_completed_total by verdict` |
| Open clarifications | Stat | `clarifications_open` |
| Evidence per task | Histogram | Logs |

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
