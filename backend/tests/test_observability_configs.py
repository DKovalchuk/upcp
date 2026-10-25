"""Observability config contracts — SPEC-0024 follow-up / TASK-0151 (red → green).

Finding (TASK-0140): collector→loki:4317 connection-refused; a top-level
``otlp:`` block is rejected by loki 3.4.2 (``field otlp not found in type
loki.ConfigWrapper``) — it was reverted to a "healthy" state while the
collector kept retrying a dead endpoint forever.

Empirical ground truth for grafana/loki:3.4.2 (TASK-0151):
- the native OTLP receiver is served on the **main HTTP port** at
  ``/otlp/v1/logs`` (ingest errors are returned, i.e. the path parses
  requests — a stale-timestamp probe produced a real Loki 400);
- ports 4317/4318 are NOT listening (``/dev/tcp`` probe: closed);
- ``otlp:`` in loki-config.yaml fails ``-verify-config``.

Pins: the collector must export logs via OTLP/HTTP to ``/otlp`` on
Loki's main port, and loki-config must not regain a top-level ``otlp:``
key. Text-level assertions (no YAML dependency), same style as
test_public_paths.py.
"""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_COLLECTOR_CFG = _ROOT / "observability" / "otel-collector-config.yaml"
_LOKI_CFG = _ROOT / "observability" / "loki-config.yaml"


def test_collector_logs_export_uses_loki_otlp_http_main_port() -> None:
    """Logs pipeline must export OTLP/HTTP to the working receiver path."""
    cfg = _COLLECTOR_CFG.read_text(encoding="utf-8")
    assert "otlphttp/loki:" in cfg, "logs exporter must be otlphttp (Loki 3.4.2 HTTP receiver)"
    assert "endpoint: http://loki:3100/otlp" in cfg, (
        "Loki 3.4.2 native OTLP lives at /otlp/v1/logs on the main HTTP port (3100) — "
        "TASK-0151; there is no separate 4317 gRPC listener"
    )
    assert "endpoint: loki:4317" not in cfg, (
        "no exporter directive may target loki's gRPC 4317 — it was "
        "connection-refused forever on loki 3.4.2 (TASK-0151); history "
        "comments mentioning the dead endpoint are allowed"
    )
    # the logs pipeline must actually reference the exporter
    logs_section = cfg.split("logs:", 1)[1] if "logs:" in cfg else ""
    assert "otlphttp/loki" in logs_section, "logs pipeline must use the otlphttp/loki exporter"


def test_loki_config_has_no_invalid_top_level_otlp_block() -> None:
    """loki 3.4.2 rejects a top-level otlp: key — guard against reintroduction."""
    lines = _LOKI_CFG.read_text(encoding="utf-8").splitlines()
    top_level_otlp = [ln for ln in lines if ln.startswith("otlp:")]
    assert not top_level_otlp, (
        "top-level otlp: fails -verify-config on grafana/loki:3.4.2 "
        "('field otlp not found in type loki.ConfigWrapper') — TASK-0151"
    )


def test_grafana_provisioning_dashboard_paths_exist() -> None:
    """Every provisioned dashboard folder must exist on disk (TASK-0152).

    Grafana walks each provider's `options.path`; a missing host dir
    (`observability/grafana/dashboards/<name>`) means the bind-mounted
    container path is missing too → provisioning walk error on startup
    (finding: `dashboards/production` never existed).
    """
    import re

    providers_dir = _ROOT / "observability" / "grafana" / "provisioning" / "dashboards"
    providers_yaml = "\n".join(
        p.read_text(encoding="utf-8") for p in sorted(providers_dir.glob("*.yaml"))
    )
    names = re.findall(r"path:\s*/etc/grafana/dashboards/([A-Za-z0-9_-]+)", providers_yaml)
    assert names, "no provisioned dashboard paths found — provisioning yml changed shape?"

    dashboards_root = _ROOT / "observability" / "grafana" / "dashboards"
    missing = [n for n in names if not (dashboards_root / n).is_dir()]
    assert not missing, (
        f"provisioned dashboard folder(s) missing on disk: {missing} — "
        "Grafana's file provider walk-errors on startup (TASK-0152)"
    )


def _compose_service_block(compose_text: str, service: str) -> str:
    """Slice a top-level (2-space) service block out of a compose file."""
    lines = compose_text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln == f"  {service}:"), -1)
    assert start >= 0, f"service {service} missing from compose file"
    end = len(lines)
    for i in range(start + 1, len(lines)):
        ln = lines[i]
        if ln.startswith("  ") and not ln.startswith("   ") and ln.rstrip().endswith(":"):
            end = i
            break
    return "\n".join(lines[start:end])


def test_compose_test_stack_exposes_pushgateway() -> None:
    """TASK-0158: security results need a push endpoint on the test stack."""
    compose = (_ROOT / "docker-compose.test.yml").read_text(encoding="utf-8")
    block = _compose_service_block(compose, "pushgateway")
    assert "prom/pushgateway" in block, "official pushgateway image"
    assert "UPCP_PORT_PUSHGATEWAY:-39092" in block, (
        "canonical UPCP_PORT_* prefix (task-0119 contract); 39092 sits next to "
        "the test-stack prometheus 39091"
    )
    assert "observability" in block, "gateway belongs to the observability profile"
    assert ":9091" in block, "pushgateway container port 9091"


def test_prometheus_scrapes_pushgateway() -> None:
    """TASK-0158: pushed security gauges must be scraped by the test Prometheus."""
    cfg = (_ROOT / "observability" / "prometheus-test.yml").read_text(encoding="utf-8")
    assert "job_name: upcp-security" in cfg, "scrape job for upcp_security_* gauges"
    assert "- pushgateway:9091" in cfg, "job must target the compose service name"


def test_security_dashboard_exists_and_queries_gauges() -> None:
    """TASK-0158 (Sec→Grafana): provisioned dashboard over the pushed series."""
    path = _ROOT / "observability" / "grafana" / "dashboards" / "test" / "security.json"
    assert path.is_file(), "observability/grafana/dashboards/test/security.json missing"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["uid"] == "upcp-test-security", "stable uid following upcp-test-* convention"
    exprs = [t.get("expr", "") for p in data.get("panels", []) for t in p.get("targets", [])]
    assert exprs, "dashboard must have panels with promql targets"
    for metric in ("upcp_security_pass", "upcp_security_findings", "upcp_security_timestamp"):
        assert any(metric in e for e in exprs), f"no panel queries {metric}"
