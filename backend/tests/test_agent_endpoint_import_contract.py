"""Import contract for the cross-context cleanup — TASK-0176 / SPEC-0029 AC7.

Assertion-level red on the old code: ``identity/agent_endpoints.py`` and
``api/v1/agent_self.py`` still import foreign-context models. Green once
both consume only the owner contexts' public service surface. The full
AST gate lives in ``test_context_boundaries.py`` (BASELINE shrunk in the
same commit).
"""

from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"


def _source(rel: str) -> str:
    return (APP_DIR / rel).read_text(encoding="utf-8")


def test_agent_endpoints_import_no_foreign_models() -> None:
    """SPEC-0029 AC7: agent_endpoints references neither delivery nor quality models."""
    src = _source("identity/agent_endpoints.py")
    assert "app.delivery.models" not in src
    assert "app.quality.models" not in src


def test_agent_self_imports_no_delivery_models() -> None:
    """SPEC-0029 AC7: agent_self references no delivery models."""
    src = _source("api/v1/agent_self.py")
    assert "app.delivery.models" not in src


def test_consumers_use_owner_service_surface() -> None:
    """The foreign reads moved behind the owning contexts' public services."""
    endpoints = _source("identity/agent_endpoints.py")
    assert "from app.delivery.service import" in endpoints
    assert "from app.quality.service import" in endpoints
    agent_self = _source("api/v1/agent_self.py")
    assert "from app.delivery.service import" in agent_self
