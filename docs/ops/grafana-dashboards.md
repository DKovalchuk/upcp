# Grafana Dashboards — Specification

> Project: UPCP | Datasources: Prometheus, Loki, Tempo

## 1. Dashboard 1: Service Health

**UID:** `upcp-service-health`
**Refresh:** 30s
**Panels:**

### 1.1 Request Rate
```
Panel: Time Series
Query: sum(rate(upcp_http_requests_total[5m])) by (method, handler)
Legend: {{method}} {{handler}}
Unit: req/s
Thresholds: green < 100, yellow < 500, red ≥ 500
```

### 1.2 Latency (p50/p95/p99)
```
Panel: Time Series
Queries:
  - histogram_quantile(0.50, sum(rate(upcp_http_request_duration_seconds_bucket[5m])) by (le))
  - histogram_quantile(0.95, sum(rate(upcp_http_request_duration_seconds_bucket[5m])) by (le))
  - histogram_quantile(0.99, sum(rate(upcp_http_request_duration_seconds_bucket[5m])) by (le))
Unit: seconds
Thresholds: green < 0.2, yellow < 1.0, red ≥ 1.0 (p95)
```

### 1.3 Error Rate
```
Panel: Gauge
Query: sum(rate(upcp_http_requests_total{status=~"5.."}[5m])) / sum(rate(upcp_http_requests_total[5m])) * 100
Unit: percent
Thresholds: green < 1, yellow < 5, red ≥ 5
```

### 1.4 Uptime
```
Panel: Stat
Query: up{job="upcp-app"}
Unit: uptime
Text: "UP" / "DOWN"
```

### 1.5 Requests by Status Code
```
Panel: Pie Chart
Query: sum(increase(upcp_http_requests_total[1h])) by (status)
```

### 1.6 Database Connection Pool
```
Panel: Gauge
Queries:
  - upcp_db_pool_active_connections
  - upcp_db_pool_idle_connections
  - upcp_db_pool_max_connections
```

## 2. Dashboard 2: Auth & Security

**UID:** `upcp-auth-security`
**Refresh:** 1m
**Panels:**

### 2.1 Login Attempts
```
Panel: Time Series
Queries:
  - sum(rate(upcp_auth_attempts_total{result="success"}[5m])) — Success
  - sum(rate(upcp_auth_attempts_total{result="failure"}[5m])) — Failure
Legend: {{result}}
```

### 2.2 Rate Limit Hits
```
Panel: Time Series
Query: sum(rate(upcp_rate_limit_hits_total[5m])) by (endpoint)
Legend: {{endpoint}}
Thresholds: yellow > 10/min, red > 50/min
```

### 2.3 Failed Auth by IP
```
Panel: Table
Query: topk(20, sum(increase(upcp_auth_attempts_total{result="failure"}[1h])) by (client_ip))
Columns: IP | Count | Last attempt
Sort: Count desc
```

### 2.4 API Key Usage
```
Panel: Time Series
Query: sum(rate(upcp_api_key_requests_total[5m])) by (key_prefix)
Legend: key {{key_prefix}}***
```

### 2.5 JWT Token Issues
```
Panel: Stat
Queries:
  - upcp_jwt_expired_total — Expired tokens
  - upcp_jwt_invalid_total — Invalid tokens
```

### 2.6 Blocked Requests
```
Panel: Logs
Datasource: Loki
Query: {job="upcp"} |= "blocked" | logfmt
Fields: timestamp, ip, endpoint, reason
```

## 3. Dashboard 3: Agent Activity

**UID:** `upcp-agent-activity`
**Refresh:** 30s
**Panels:**

### 3.1 Active Claims
```
Panel: Stat
Query: upcp_tasks_active{status="claimed"}
Unit: short
Sparkline: enabled
```

### 3.2 Heartbeat Status
``Panel: Time Series
Queries:
  - sum(upcp_heartbeat_total) by (status) — healthy/stale/dead
Colors: green=healthy, yellow=stale, red=dead
```

### 3.3 Stale Detections
```
Panel: Time Series
Query: sum(rate(upcp_tasks_stale_total[5m]))
Thresholds: green < 0.1, yellow < 1, red ≥ 1 (per 5min)
```

### 3.4 Clarifications Active
```
Panel: Stat
Query: upcp_clarifications_active
Unit: short
```

### 3.5 Agent Task Cycle Time
```
Panel: Histogram
Query: histogram_quantile(0.50, sum(rate(upcp_task_cycle_seconds_bucket[1h])) by (le))
Unit: minutes
Legend: p50, p95
```

### 3.6 Claims by Agent
```
Panel: Table
Query: sum(upcp_tasks_active) by (agent_id)
Columns: Agent | Active Claims | Last Heartbeat
Sort: Active Claims desc
```

### 3.7 Agent Inbox Messages
```
Panel: Time Series
Query: sum(rate(upcp_inbox_messages_total[5m])) by (priority)
Legend: {{priority}}
```

## 4. Dashboard 4: Delivery & Quality

**UID:** `upcp-delivery-quality`
**Refresh:** 5m
**Panels:**

### 4.1 Tasks by Status
```
Panel: Stacked Bar
Query: upcp_tasks_total by (status)
Colors: open=blue, claimed=yellow, in_progress=cyan, blocked=red, in_review=purple, done=green
```

### 4.2 Evidence Completeness
```
Panel: Gauge
Query: avg(upcp_evidence_completeness_percent)
Unit: percent
Thresholds: red < 50, yellow < 80, green ≥ 80
```

### 4.3 Review Turnaround
```
Panel: Time Series
Query: avg(upcp_review_turnaround_seconds) by (reviewer_type)
Unit: minutes
Legend: {{reviewer_type}}
```

### 4.4 First-Pass Approval Rate
```
Panel: Gauge
Query: sum(rate(upcp_review_rounds_total{round=1,result="approved"}[7d])) / sum(rate(upcp_review_rounds_total{round=1}[7d])) * 100
Unit: percent
Thresholds: red < 50, yellow < 75, green ≥ 75
```

### 4.5 Finding Density
```
Panel: Time Series
Query: sum(rate(upcp_findings_total[7d])) / sum(rate(upcp_review_rounds_total[7d]))
Legend: findings/review
```

### 4.6 Velocity (Tasks Done per Day)
```
Panel: Time Series
Query: sum(increase(upcp_tasks_total{status="done"}[1d]))
Legend: tasks/day
Trend: 7-day moving average overlay
```

### 4.7 Quality Gate Results
```
Panel: Stacked Bar
Query: sum(increase(upcp_quality_gate_runs_total[1d])) by (gate, result)
Legend: {{gate}} — {{result}}
Colors: pass=green, fail=red
```

## 5. General Settings

### Variables

| Variable | Query | Description |
|----------|-------|-------------|
| `$project` | `label_values(upcp_tasks_total, project)` | Project filter |
| `$agent` | `label_values(upcp_tasks_active, agent_id)` | Agent filter |
| `$interval` | `1m, 5m, 15m, 1h` | Aggregation interval |

### Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| High error rate | error_rate > 5% for 5m | critical |
| Stale tasks spike | stale_detections > 5 in 10m | warning |
| No heartbeats | heartbeat_rate == 0 for 3m | critical |
| Review backlog | in_review_count > 20 for 15m | warning |
| Auth failure spike | auth_failures > 100 in 5m | critical |
| DB pool exhausted | idle_connections < 2 for 5m | warning |
