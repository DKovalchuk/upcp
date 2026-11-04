"""API surface classification contract — SPEC-0028 §3.1 / TASK-0168 (red → green).

Classification is composition-time data (SPEC-0028 D2): every registered
route must belong to exactly one surface — web (JWT), agent (API key) or
public. Unclassified routes fail here — the structural fix for the
finding-2/9 class: auth must not depend on path-string guards, and a
route invisible to classification must be a test failure, not a silent
unauthenticated endpoint.
"""

from app.api.registry import (
    AGENT_ROUTERS,
    PUBLIC_APP_PATHS,
    PUBLIC_ROUTERS,
    WEB_ROUTERS,
    route_surface,
)
from fastapi import APIRouter
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute


def _app_routes() -> list[BaseRoute]:
    from app.main import app  # production wiring

    return list(app.routes)


def _groups():
    for surface, routers in (
        ("web", WEB_ROUTERS),
        ("agent", AGENT_ROUTERS),
        ("public", PUBLIC_ROUTERS),
    ):
        for router, prefix in routers:
            yield surface, router, prefix


def test_every_registered_route_is_classified() -> None:
    """Completeness: no registered route may be invisible to classification."""
    unclassified = sorted(
        p for r in _app_routes() if (p := getattr(r, "path", None)) and route_surface(r) is None
    )
    assert unclassified == [], (
        "unclassified routes (web/agent/public): "
        f"{unclassified} — register their router in app/api/registry.py"
    )


def test_surface_groups_are_disjoint() -> None:
    """No endpoint may be claimed by two surfaces (blanket deps would double-apply)."""
    owners: dict[int, tuple[str, str]] = {}
    conflicts: list[str] = []
    for surface, router, _prefix in _groups():
        for route in router.routes:
            if not isinstance(route, APIRoute) or route.endpoint is None:
                continue
            key = id(route.endpoint)
            owner = owners.get(key)
            if owner is not None and owner[0] != surface:
                conflicts.append(f"{route.path}: {owner[0]} vs {surface}")
            owners[key] = (surface, route.path)
    assert conflicts == []


def test_group_mount_prefixes_match_surface_contract() -> None:
    """WEB — /api/v1 + /auth; AGENT — /api/v1 + /mcp; PUBLIC — /auth (+ app-level paths)."""
    allowed = {"web": {"/api/v1", "/auth"}, "agent": {"/api/v1", "/mcp"}, "public": {"/auth"}}
    for surface, _router, prefix in _groups():
        assert prefix in allowed[surface], f"{surface} router mounted at {prefix}"


def test_public_app_paths_exist_and_resolve_public() -> None:
    """Continuity with SPEC-0027 AC7: dead public-path entries are prohibited."""
    routes = _app_routes()
    paths = {p for r in routes if (p := getattr(r, "path", None)) is not None}
    missing = sorted(p for p in PUBLIC_APP_PATHS if p not in paths)
    assert missing == [], f"dead PUBLIC_APP_PATHS entries: {missing}"
    for route in routes:
        if getattr(route, "path", None) in PUBLIC_APP_PATHS:
            assert route_surface(route) == "public"


def test_unregistered_endpoint_is_detected_as_unclassified() -> None:
    """Mutation-style negative: a router missing from the registry must fail."""
    api = APIRouter()

    @api.get("/synthetic-unregistered")
    def _synthetic() -> None:  # pragma: no cover
        return None

    assert route_surface(api.routes[0]) is None


# ── D5 amendment (TASK-0179): workflow read-backs are a UI feature ────────
# The e2e gate caught the classification gap: the Execution/Clarifications
# tabs list these with a JWT, so they belong to the web surface — while
# every workflow WRITE stays agent-key-only.


_WORKFLOW_READS = (
    "GET /api/v1/tasks/{task_id}/claims",
    "GET /api/v1/tasks/{task_id}/heartbeats",
    "GET /api/v1/tasks/{task_id}/clarifications",
)
_WORKFLOW_WRITES = (
    "POST /api/v1/tasks/{task_id}/claim",
    "POST /api/v1/tasks/{task_id}/release",
    "POST /api/v1/tasks/{task_id}/heartbeat",
    "POST /api/v1/tasks/{task_id}/progress",
    "POST /api/v1/tasks/{task_id}/clarifications",
    "POST /api/v1/clarifications/{clarification_id}/answer",
)


def _path_surface(method: str, path: str) -> str | None:
    """Surface of ``METHOD path`` from the registry group composition.

    ``app.routes`` holds lazy ``_IncludedRouter`` wrappers (FastAPI >= 0.139)
    whose inner routes carry no mount prefix — the group tuples ARE the
    classification source of truth, so the split contract is checked there.
    """
    for surface, routers in (
        ("web", WEB_ROUTERS),
        ("agent", AGENT_ROUTERS),
        ("public", PUBLIC_ROUTERS),
    ):
        for router, prefix in routers:
            for route in router.routes:
                if not isinstance(route, APIRoute):
                    continue
                if prefix + route.path == path and method in (route.methods or set()):
                    return surface
    return None


def test_workflow_reads_classify_as_web() -> None:
    """UI read-backs authenticate with a JWT (the e2e regression net)."""
    for target in _WORKFLOW_READS:
        method, path = target.split(" ", 1)
        surface = _path_surface(method, path)
        assert surface == "web", f"{target} must be web-surface, got {surface!r}"


def test_workflow_writes_stay_agent() -> None:
    """Workflow mutations stay agent-key-only + agent:workflow scope (AC6)."""
    for target in _WORKFLOW_WRITES:
        method, path = target.split(" ", 1)
        surface = _path_surface(method, path)
        assert surface == "agent", f"{target} must be agent-surface, got {surface!r}"
