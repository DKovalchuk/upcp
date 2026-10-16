"""Prometheus metrics — counters, histograms, gauges for application observability."""

from prometheus_client import Counter, Gauge, Histogram, Info

# ── HTTP Metrics ──────────────────────────────────────────────

http_requests_total = Counter(
    "upcp_http_requests_total",
    "Total HTTP requests",
    ["method", "handler", "status"],
)

http_request_duration_seconds = Histogram(
    "upcp_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "handler"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "upcp_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method"],
)

# ── Business Metrics ──────────────────────────────────────────

tasks_active = Gauge(
    "upcp_tasks_active",
    "Number of active tasks by status",
    ["status"],
)

heartbeat_total = Counter(
    "upcp_heartbeat_total",
    "Total heartbeats received",
    ["status"],
)

auth_attempts_total = Counter(
    "upcp_auth_attempts_total",
    "Total authentication attempts",
    ["result"],
)

claims_total = Counter(
    "upcp_claims_total",
    "Total task claim attempts",
    ["result"],
)

evidence_uploads_total = Counter(
    "upcp_evidence_uploads_total",
    "Total evidence uploads",
    ["file_type"],
)

# ── Infrastructure Metrics ────────────────────────────────────

rate_limit_hits_total = Counter(
    "upcp_rate_limit_hits_total",
    "Total rate limit rejections",
    ["endpoint"],
)

db_pool_connections = Gauge(
    "upcp_db_pool_connections",
    "Database connection pool state",
    ["state"],
)

redis_operations_total = Counter(
    "upcp_redis_operations_total",
    "Total Redis operations",
    ["operation", "result"],
)

# ── Application Info ──────────────────────────────────────────

app_info = Info(
    "upcp_app",
    "Application version and environment info",
)
