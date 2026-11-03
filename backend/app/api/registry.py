"""API surface registry — composition-time route classification (SPEC-0028 §3.1).

Single source of truth for which router belongs to which API surface.
Classification data + surface-level auth attachment: the WEB group carries
``Depends(web_auth)`` through ``include_surfaces`` since TASK-0169 —
SPEC-0028 D2 forbids path-string matching anywhere in authentication; the
AGENT group attaches its dependency in TASK-0170, the PUBLIC group never.

Surfaces (SPEC-0028 D5):

- ``web``    — browser API, authenticates with a JWT;
- ``agent``  — agent API (MCP today), authenticates with an agent API key;
- ``public`` — declared no-auth routes: composition-time declaration
  checked by ``tests/test_api_surface_registry.py`` (a route outside all
  groups fails the contract instead of silently running unauthenticated).
"""

from fastapi import APIRouter, Depends, FastAPI

from app.api.v1.agent_self import router as agent_self_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.audit import router as audit_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.gitread import router as gitread_router
from app.api.v1.notification_channels import router as notification_channels_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.reaper import router as reaper_router
from app.api.v1.reporting import router as reporting_router
from app.api.v1.search import router as search_router
from app.api.v1.structure import router as structure_router
from app.api.v1.task_workflow import router as workflow_router
from app.identity.agent_endpoints import router as agent_admin_router
from app.identity.dependencies import get_web_auth
from app.identity.endpoints import public_router as auth_public_router
from app.identity.endpoints import router as auth_protected_router
from app.mcp.server import create_mcp_router

API_PREFIX = "/api/v1"
MCP_PREFIX = "/mcp"
AUTH_PREFIX = "/auth"

mcp_router = create_mcp_router()

# (router, mount prefix) per surface — groups must stay disjoint.
WEB_ROUTERS: tuple[tuple[APIRouter, str], ...] = (
    (projects_router, API_PREFIX),
    (structure_router, API_PREFIX),
    (delivery_router, API_PREFIX),
    (quality_router, API_PREFIX),
    (gitread_router, API_PREFIX),
    (reporting_router, API_PREFIX),
    (dashboard_router, API_PREFIX),
    (audit_router, API_PREFIX),
    (search_router, API_PREFIX),
    (notifications_router, API_PREFIX),
    (notification_channels_router, API_PREFIX),
    (analytics_router, API_PREFIX),
    # agent MANAGEMENT is an admin web-UI feature (D5): JWT surface
    (agent_admin_router, API_PREFIX),
    (reaper_router, API_PREFIX),
    (auth_protected_router, AUTH_PREFIX),
)

AGENT_ROUTERS: tuple[tuple[APIRouter, str], ...] = (
    (agent_self_router, API_PREFIX),
    (workflow_router, API_PREFIX),
    (mcp_router, MCP_PREFIX),
)

PUBLIC_ROUTERS: tuple[tuple[APIRouter, str], ...] = ((auth_public_router, AUTH_PREFIX),)

# App-level (non-router) routes that are public by declaration.
PUBLIC_APP_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/api/v1/health",
        "/metrics",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
    }
)


def include_surfaces(app: FastAPI) -> None:
    """Mount every classified router with its declared prefix.

    The WEB group carries the ``web_auth`` blanket dependency — default
    deny for every route of the surface (SPEC-0028 D2, TASK-0169); the
    dependency resolves through identity's public surface
    (``dependencies.get_web_auth``) so the composition root never reaches
    into context internals. The AGENT and PUBLIC groups mount bare: agent
    auth lands in TASK-0170, public is declared no-auth.
    """
    web_deps = [Depends(get_web_auth())]
    for group, deps in ((WEB_ROUTERS, web_deps), (AGENT_ROUTERS, []), (PUBLIC_ROUTERS, [])):
        for router, prefix in group:
            app.include_router(router, prefix=prefix, dependencies=deps)


_endpoint_surfaces: dict[int, str] = {}
_router_surfaces: dict[int, str] = {}


def _build_indexes() -> None:
    for surface, group in (
        ("web", WEB_ROUTERS),
        ("agent", AGENT_ROUTERS),
        ("public", PUBLIC_ROUTERS),
    ):
        for router, _prefix in group:
            _router_surfaces[id(router)] = surface
            for route in router.routes:
                endpoint = getattr(route, "endpoint", None)
                if endpoint is None:
                    continue
                key = id(endpoint)
                existing = _endpoint_surfaces.get(key)
                if existing is not None and existing != surface:
                    raise RuntimeError(
                        f"endpoint registered in surfaces {existing!r} and {surface!r} — "
                        "surface groups must be disjoint (SPEC-0028 S28.1)"
                    )
                _endpoint_surfaces[key] = surface


_build_indexes()


def route_surface(route: object) -> str | None:
    """Surface of a registered route: ``"web" | "agent" | "public" | None``.

    ``None`` means unclassified — a contract-test failure for production
    routes. FastAPI >= 0.139 includes routers lazily: ``app.routes`` holds
    ``_IncludedRouter`` wrappers whose ``original_router`` identifies the
    surface. App-level routes are matched by exact public path; raw
    router-level ``APIRoute``s (synthetic/direct) fall back to endpoint
    identity.
    """
    included_router = getattr(route, "original_router", None)
    if included_router is not None:
        return _router_surfaces.get(id(included_router))
    path = getattr(route, "path", None)
    if path in PUBLIC_APP_PATHS:
        return "public"
    endpoint = getattr(route, "endpoint", None)
    if endpoint is not None:
        return _endpoint_surfaces.get(id(endpoint))
    return None
