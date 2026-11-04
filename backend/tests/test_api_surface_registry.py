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
