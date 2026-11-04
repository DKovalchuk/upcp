"""MCP server implementation.

JSON-RPC dispatch with principal binding (SPEC-0028 §3.4, AC5 /
TASK-0171): the ``tools/call`` route receives the Starlette ``Request``
stamped by the agent-auth blanket (``request.state.agent_id``, TASK-0170)
and every tools/call is checked against it BEFORE any handler runs.

Binding rule (auth on, i.e. ``settings.disable_auth`` is false):

- a ``tools/call`` without a principal is refused — fail-closed for
  mis-mounted routers that reach the handler with no auth context;
- EVERY declared identity argument present in the call must EQUAL the
  principal (``IDENTITY_ARGS``: ``agent_id``, ``answered_by``,
  ``created_by_id``), and every tool whose schema DECLARES ``agent_id``
  must receive it;
- refusals answer a JSON-RPC error (``-32001``) inside the normal
  HTTP 200 response — protocol-correct for tool-level refusals — plus a
  structured warning (``action=auth.principal_mismatch``) and span
  attributes (``upcp.auth.principal_mismatch`` / ``upcp.auth.sub``).

Under the hermetic ``disable_auth`` flag the binding is skipped entirely
(legacy behavior — bare ``create_mcp_router()`` test mounts keep working).

A class-guard test scans ``get_tools()`` schemas with an identity-ish
regex and fails until every match is declared in ``IDENTITY_ARGS`` — a
future tool introducing a new identity argument cannot silently sit
outside the binding.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.identity.dependencies import get_require_agent_scope
from app.mcp.resources import get_resource_content, get_resources
from app.mcp.schemas import (
    JSONRPCRequest,
    JSONRPCResponse,
)
from app.mcp.tools import call_tool, get_tools
from app.shared.config import get_settings
from app.shared.database import get_session
from app.shared.logging import get_logger

logger = get_logger(__name__)

# JSON-RPC application error for principal refusals (-32000..-32999 range)
JSONRPC_FORBIDDEN = -32001
_MSG_MISMATCH = "Forbidden: agent identity mismatch"
_MSG_NO_PRINCIPAL = "Forbidden: no authenticated principal"

# Binding inventory: tools whose schema declares an ``agent_id`` argument
# (derived from get_tools() — pinned as a set by the TASK-0171 evidence test).
_AGENT_ID_TOOLS = frozenset(
    tool.name for tool in get_tools() if "agent_id" in tool.input_schema.properties
)

# Declared identity arguments (SPEC-0028 §3.4): every call argument whose
# value IS (or claims to be) an agent identity must equal the authenticated
# principal. ``agent_id`` is the historical inventory; ``answered_by``
# (answer_clarification) and ``created_by_id`` (attach_evidence) were added
# by the aspect review — they carried identity outside the binding and were
# spoofable. Pinned by the class-guard test in test_mcp_principal_binding
# (regex match over get_tools() must equal this map's keys exactly).
IDENTITY_ARGS: dict[str, str] = {
    "agent_id": "acting agent (claim/release/heartbeat/inbox/… tools)",
    "answered_by": "answering agent (answer_clarification)",
    "created_by_id": "creating agent (attach_evidence)",
}


class PrincipalBindingError(Exception):
    """tools/call refused: identity not bound to the authenticated principal."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.code = JSONRPC_FORBIDDEN
        self.message = message


def _observe_binding_refusal(reason: str, principal: str | None, tool_name: str) -> None:
    """Structured refusal telemetry (agent_auth/permissions.py style)."""
    logger.warning(
        "MCP principal binding refused tool=%s principal=%s reason=%s",
        tool_name,
        principal,
        reason,
        extra={"action": "auth.principal_mismatch", "entity_type": "agent"},
    )
    try:
        from opentelemetry import trace
    except ImportError:  # pragma: no cover — opentelemetry optional
        trace = None  # type: ignore[assignment]
    if trace is not None:
        span = trace.get_current_span()
        if span.is_recording():
            attributes: dict[str, str | bool] = {"upcp.auth.principal_mismatch": True}
            if principal is not None:
                attributes["upcp.auth.sub"] = principal
            span.set_attributes(attributes)


def _enforce_principal_binding(
    tool_name: str, arguments: dict[str, object], request: Request
) -> None:
    """Bind tools/call identity to the authenticated principal (AC5).

    Fail-closed while auth is on: missing principal → refuse; every
    declared identity argument PRESENT in the call must equal
    ``request.state.agent_id`` (string compare), and a tool whose schema
    DECLARES ``agent_id`` must receive it (absence counts as a mismatch —
    the historical contract). Skipped entirely under the hermetic
    ``disable_auth`` flag — parity with the blanket and scope gate,
    preserving bare ``create_mcp_router()`` mounts.
    """
    if get_settings().disable_auth:
        return  # hermetic kill switch (AC10, documented test-only)
    raw_principal = getattr(request.state, "agent_id", None)
    principal = str(raw_principal) if raw_principal else None
    if principal is None:
        _observe_binding_refusal("missing-principal", None, tool_name)
        raise PrincipalBindingError(_MSG_NO_PRINCIPAL)
    spoofed_identity = any(
        arg in arguments and str(arguments.get(arg)) != principal for arg in IDENTITY_ARGS
    )
    missing_declared_agent_id = tool_name in _AGENT_ID_TOOLS and "agent_id" not in arguments
    if spoofed_identity or missing_declared_agent_id:
        _observe_binding_refusal("mismatch", principal, tool_name)
        raise PrincipalBindingError(_MSG_MISMATCH)


def _handle_initialize(payload: JSONRPCRequest) -> JSONRPCResponse:
    """Handle initialize method."""
    result: dict[str, Any] = {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {},
            "resources": {},
        },
        "serverInfo": {
            "name": "upcp-mcp-server",
            "version": "1.0.0",
        },
    }
    return JSONRPCResponse(jsonrpc="2.0", id=payload.id, result=result)


def _handle_tools_list(payload: JSONRPCRequest) -> JSONRPCResponse:
    """Handle tools/list method."""
    tools = get_tools()
    result: dict[str, Any] = {"tools": [tool.model_dump() for tool in tools]}
    return JSONRPCResponse(jsonrpc="2.0", id=payload.id, result=result)


async def _handle_tools_call(
    payload: JSONRPCRequest, session: Session, request: Request
) -> JSONRPCResponse:
    """Handle tools/call method — principal binding runs before dispatch."""
    if not payload.params or "name" not in payload.params:
        raise ValueError("Missing tool name")

    tool_name = str(payload.params["name"])
    raw_args = payload.params.get("arguments")
    arguments: dict[str, object] = dict(raw_args) if isinstance(raw_args, dict) else {}

    _enforce_principal_binding(tool_name, arguments, request)

    tool_result = await call_tool(tool_name, arguments, session=session)
    result: dict[str, object] = tool_result.model_dump()
    return JSONRPCResponse(jsonrpc="2.0", id=payload.id, result=result)


def _handle_resources_list(payload: JSONRPCRequest) -> JSONRPCResponse:
    """Handle resources/list method."""
    resources = get_resources()
    result: dict[str, Any] = {"resources": [res.model_dump() for res in resources]}
    return JSONRPCResponse(jsonrpc="2.0", id=payload.id, result=result)


def _handle_resources_read(payload: JSONRPCRequest) -> JSONRPCResponse:
    """Handle resources/read method."""
    if not payload.params or "uri" not in payload.params:
        raise ValueError("Missing resource URI")

    uri = str(payload.params["uri"])
    project_id_val = payload.params.get("project_id")
    project_id = str(project_id_val) if project_id_val is not None else None

    content = get_resource_content(uri, project_id)
    result: dict[str, Any] = {"contents": [{"uri": uri, "mimeType": "text/plain", "text": content}]}
    return JSONRPCResponse(jsonrpc="2.0", id=payload.id, result=result)


def _handle_method_not_found(payload: JSONRPCRequest) -> JSONRPCResponse:
    """Handle unknown methods."""
    error: dict[str, Any] = {"code": -32601, "message": f"Method not found: {payload.method}"}
    return JSONRPCResponse(jsonrpc="2.0", id=payload.id, error=error)


async def _dispatch_jsonrpc(
    payload: JSONRPCRequest, session: Session, request: Request
) -> JSONRPCResponse:
    """Dispatch JSON-RPC request to appropriate handler."""
    method = payload.method

    if method == "initialize":
        return _handle_initialize(payload)
    if method == "tools/list":
        return _handle_tools_list(payload)
    if method == "tools/call":
        return await _handle_tools_call(payload, session, request)
    if method == "resources/list":
        return _handle_resources_list(payload)
    if method == "resources/read":
        return _handle_resources_read(payload)
    return _handle_method_not_found(payload)


def create_mcp_router() -> APIRouter:
    """Create MCP router with endpoints.

    The router carries the ``agent:mcp`` scope gate (SPEC-0028 AC6,
    TASK-0170) — agent-key-only surface, resolved through identity's
    public accessor. The gate is inert under the hermetic
    ``disable_auth`` flag, so bare test mounts keep working.

    The ``POST /`` handler additionally runs the principal binding
    (SPEC-0028 AC5, TASK-0171): with auth on it requires
    ``request.state.agent_id`` and refuses ``tools/call`` whose
    ``agent_id`` argument disagrees with it (JSON-RPC ``-32001``).
    """
    require_scope = get_require_agent_scope()
    router = APIRouter(dependencies=[Depends(require_scope("agent:mcp"))])

    @router.get("/")
    def mcp_health() -> dict[str, str]:
        """MCP health endpoint."""
        return {"status": "ok", "service": "mcp-server"}

    @router.post("/")
    async def handle_jsonrpc(
        payload: JSONRPCRequest,
        request: Request,
        session: Session = Depends(get_session),  # noqa: B008
    ) -> JSONResponse:
        """Handle JSON-RPC 2.0 requests (binds tools/call to the principal)."""
        try:
            response = await _dispatch_jsonrpc(payload, session, request)
        except PrincipalBindingError as exc:
            error: dict[str, Any] = {"code": exc.code, "message": exc.message}
            response = JSONRPCResponse(jsonrpc="2.0", id=payload.id, error=error)
        except Exception as e:
            error = {"code": -32603, "message": str(e)}
            response = JSONRPCResponse(jsonrpc="2.0", id=payload.id, error=error)

        return JSONResponse(content=response.model_dump())

    @router.get("/tools")
    def list_tools() -> dict[str, list[dict[str, object]]]:
        """List available tools."""
        tools = get_tools()
        return {"tools": [tool.model_dump() for tool in tools]}

    @router.get("/tools/{tool_name}")
    def get_tool(tool_name: str) -> dict[str, object]:
        """Get tool by name."""
        tools = get_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool.model_dump()
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

    @router.get("/resources")
    def list_resources() -> dict[str, list[dict[str, object]]]:
        """List available resources."""
        resources = get_resources()
        return {"resources": [res.model_dump() for res in resources]}

    @router.get("/resources/{resource_name}")
    def get_resource(resource_name: str, project_id: str | None = None) -> dict[str, object]:
        """Get resource by name."""
        resources = get_resources()
        for res in resources:
            if resource_name in res.uri:
                content = get_resource_content(res.uri, project_id)
                return {"content": content}
        raise HTTPException(status_code=404, detail=f"Resource {resource_name} not found")

    return router
