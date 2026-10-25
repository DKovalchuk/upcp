"""Bootstrap scaffold port-var contract — TASK-0156 (TASK-0119 follow-up).

The scaffolder's generated templates must emit the canonical
``UPCP_PORT_*`` prefix (the TASK-0119 contract), never the legacy
``UPCP_HTTP_PORT``-style names the root compose migrated away from.
"""

import bootstrap_upcp

LEGACY_PORT_VARS = (
    "UPCP_HTTP_PORT",
    "UPCP_POSTGRES_PORT",
    "UPCP_PROMETHEUS_PORT",
    "UPCP_GRAFANA_PORT",
    "UPCP_FRONTEND_DEV_PORT",
)

CANONICAL_ENV_VARS = (
    "UPCP_PORT_BACKEND",
    "UPCP_PORT_POSTGRES",
    "UPCP_PORT_PROMETHEUS",
    "UPCP_PORT_GRAFANA",
    "UPCP_PORT_FRONTEND_DEV",
)

COMPOSE_CANONICAL_VARS = (
    "UPCP_PORT_BACKEND",
    "UPCP_PORT_PROMETHEUS",
    "UPCP_PORT_GRAFANA",
)


def _assert_no_legacy(text: str, where: str) -> None:
    for name in LEGACY_PORT_VARS:
        assert name not in text, f"legacy port var {name} still present in {where}"


def test_env_example_uses_canonical_port_vars() -> None:
    env = bootstrap_upcp.FILES[".env.example"]
    for name in CANONICAL_ENV_VARS:
        assert name in env, f"canonical {name} missing from .env.example"
    _assert_no_legacy(env, ".env.example")


def test_compose_uses_canonical_port_vars() -> None:
    compose = bootstrap_upcp.FILES["docker-compose.yml"]
    for name in COMPOSE_CANONICAL_VARS:
        assert name in compose, f"canonical {name} missing from docker-compose.yml"
    _assert_no_legacy(compose, "docker-compose.yml")


def test_generated_ports_doc_lists_canonical_vars() -> None:
    doc = bootstrap_upcp.FILES["docs/11-docker-and-ports.md"]
    for name in CANONICAL_ENV_VARS:
        assert f"`{name}`" in doc, f"canonical {name} missing from docs/11 table"
    _assert_no_legacy(doc, "docs/11-docker-and-ports.md")
