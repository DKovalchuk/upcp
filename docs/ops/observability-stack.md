# Observability Stack — Setup

> Project: UPCP | Stack: OpenTelemetry, Prometheus, Grafana, Loki, Tempo

## 1. Architecture

```
┌──────────┐     ┌───────────────────┐     ┌────────────┐
│   app    │────▶│  OTel Collector   │────▶│ Prometheus │
│ (FastAPI)│     │   (receiver)      │     │  (metrics) │
└──────────┘     └────────┬──────────┘     └────────────┘
                          │
                   ┌──────▼──────┐     ┌────────────┐
                   │    Loki     │     │   Tempo    │
                   │   (logs)    │     │  (traces)  │
                   └─────────────┘     └────────────┘
                          │                  │
                   ┌──────▼──────────────────▼──┐
                   │         Grafana             │
                   │    (dashboards)             │
                   └─────────────────────────────┘
```

## 2. OpenTelemetry Collector

### 2.1 Configuration

File: `observability/otel-collector-config.yaml`

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: upcp

  otlphttp/loki:
    # Native OTLP = HTTP on Loki's MAIN port (/otlp → /v1/logs); the
    # gRPC-4317 receiver does not exist in grafana/loki:3.4.2 and a
    # top-level `otlp:` config key fails -verify-config (TASK-0151).
    endpoint: http://loki:3100/otlp

  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000

  attributes:
    actions:
      - key: service.name
        value: upcp
        action: upsert

service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch, attributes]
      exporters: [prometheus]
    traces:
      receivers: [otlp]
      processors: [batch, attributes]
      exporters: [otlp/tempo]
    logs:
      receivers: [otlp]
      processors: [batch, attributes]
      exporters: [otlphttp/loki]
```

### 2.2 Docker Compose

```yaml
otel-collector:
  image: otel/opentelemetry-collector-contrib:latest
  command: ["--config", "/etc/otel/config.yaml"]
  volumes:
    - ./observability/otel-collector-config.yaml:/etc/otel/config.yaml:ro
  ports:
    - "4317:4317"   # gRPC
    - "4318:4318"   # HTTP
    - "8889:8889"   # Prometheus export
  profiles:
    - observability
```

## 3. Prometheus

### 3.1 Scrape config

File: `observability/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "upcp-app"
    static_configs:
      - targets: ["app:8000"]
    metrics_path: /metrics

  - job_name: "upcp-otel"
    static_configs:
      - targets: ["otel-collector:8889"]

  - job_name: "upcp-redis"
    static_configs:
      - targets: ["redis-exporter:9121"]

  - job_name: "upcp-postgres"
    static_configs:
      - targets: ["postgres-exporter:9187"]
```

### 3.2 Docker Compose

```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "39090:9090"
  volumes:
    - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - promdata:/prometheus
  profiles:
    - observability
```

## 4. Grafana

### 4.1 Datasource provisioning

File: `observability/grafana/provisioning/datasources/datasources.yaml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    editable: false
```

### 4.2 Dashboard provisioning

File: `observability/grafana/provisioning/dashboards/dashboards.yaml`

```yaml
apiVersion: 1

providers:
  - name: UPCP Test
    orgId: 1
    folder: UPCP Test Environment
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /etc/grafana/dashboards/test
      foldersFromFilesStructure: false

  - name: UPCP Production
    orgId: 1
    folder: UPCP Production
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /etc/grafana/dashboards/production
      foldersFromFilesStructure: false
```

Both `dashboards/test/` and `dashboards/production/` must exist on disk
(`observability/grafana/dashboards/…`, bind-mounted to
`/etc/grafana/dashboards`) — otherwise Grafana logs
`failed to walk provisioned dashboards` every update interval. The
folders are kept with `.gitkeep` placeholders; contract-tested in
`backend/tests/test_observability_configs.py` (TASK-0152).

### 4.3 Admin access

- UI: `http://localhost:<UPCP_PORT_GRAFANA>` (test env: **33001**),
  user `admin`.
- **Password is seeded once** into the grafana volume from
  `GF_SECURITY_ADMIN_PASSWORD` at first start (init-once). **Compose
  precedence: process (shell) env > `--env-file` > default** — a shell
  carrying `GRAFANA_ADMIN_PASSWORD=admin_change_me` (root `.env` loaded
  by the launcher) overrides `.env.test`'s `admin_test` at
  interpolation; both paths probed live (TASK-0152): leak-seeded →
  `admin_change_me` 200, clean env (`env -u …` + volume reset) →
  `admin_test` 200. Reset:
  `docker volume rm <compose-project>_grafana-test-data` (grafana
  restarts, re-seeds, dashboards re-provision from the files above).

## 5. Loki

### 5.1 Configuration

File: `observability/loki-config.yaml`

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h
```

### 5.2 Docker Compose

```yaml
loki:
  image: grafana/loki:latest
  volumes:
    - ./observability/loki-config.yaml:/etc/loki/config.yaml:ro
    - lokidata:/loki
  ports:
    - "3100:3100"
  profiles:
    - observability
```

## 6. Tempo

### 6.1 Configuration

File: `observability/tempo-config.yaml`

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
    wal:
      path: /var/tempo/wal
```

### 6.2 Docker Compose

```yaml
tempo:
  image: grafana/tempo:latest
  command: ["-config.file=/etc/tempo/config.yaml"]
  volumes:
    - ./observability/tempo-config.yaml:/etc/tempo/config.yaml:ro
    - tempodata:/var/tempo
  ports:
    - "3200:3200"
    - "4317:4317"
  profiles:
    - observability
```

## 7. Application Instrumentation

### 7.1 Python (FastAPI)

```python
# src/upcp/telemetry.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_telemetry(service_name: str, otlp_endpoint: str):
    # Traces
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
    )
    trace.set_tracer_provider(tracer_provider)

    # Metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint)
    )
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
```

### 7.2 Key Application Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `upcp_http_requests_total` | counter | Total HTTP requests |
| `upcp_http_request_duration_seconds` | histogram | Request latency |
| `upcp_tasks_active` | gauge | Active tasks |
| `upcp_tasks_stale_total` | counter | Stale detections |
| `upcp_heartbeat_total` | counter | Heartbeats received |
| `upcp_review_rounds_total` | counter | Review rounds completed |
| `upcp_auth_failures_total` | counter | Failed auth attempts |

## 8. Launch

```bash
# App only
docker compose up -d

# With full observability stack
docker compose --profile observability up -d

# Verify endpoints
curl http://localhost:39090/api/v1/status/config  # Prometheus
curl http://localhost:33000/api/health             # Grafana
curl http://localhost:3100/ready                   # Loki
curl http://localhost:3200/ready                   # Tempo
```

## 9. Ports (observability)

| Service | Port | Purpose |
|--------|------|-----------|
| OTel Collector | 4317 | gRPC receiver |
| OTel Collector | 4318 | HTTP receiver |
| OTel Collector | 8889 | Prometheus metrics |
| Prometheus | 39090 | UI + API |
| Grafana | 33000 | UI |
| Loki | 3100 | Log API |
| Tempo | 3200 | Trace API |
