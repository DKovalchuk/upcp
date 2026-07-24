"""MCP server implementation."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.mcp.resources import get_resource_content, get_resources
from app.mcp.schemas import (
    JSONRPCRequest,
    JSONRPCResponse,
)
from app.mcp.tools import call_tool, get_tools
from app.shared.database import get_session


def _handle_initialize(request: JSONRPCRequest) -> JSONRPCResponse:
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
    return JSONRPCResponse(jsonrpc="2.0", id=request.id, result=result)


def _handle_tools_list(request: JSONRPCRequest) -> JSONRPCResponse:
    """Handle tools/list method."""
    tools = get_tools()
    result: dict[str, Any] = {"tools": [tool.model_dump() for tool in tools]}
    return JSONRPCResponse(jsonrpc="2.0", id=request.id, result=result)


async def _handle_tools_call(request: JSONRPCRequest, session: Session) -> JSONRPCResponse:
    """Handle tools/call method."""
    if not request.params or "name" not in request.params:
        raise ValueError("Missing tool name")

    tool_name = str(request.params["name"])
    raw_args = request.params.get("arguments")
    arguments: dict[str, object] = dict(raw_args) if isinstance(raw_args, dict) else {}

    tool_result = await call_tool(tool_name, arguments, session=session)
    result: dict[str, Any] = tool_result.model_dump()
    return JSONRPCResponse(jsonrpc="2.0", id=request.id, result=result)


def _handle_resources_list(request: JSONRPCRequest) -> JSONRPCResponse:
    """Handle resources/list method."""
    resources = get_resources()
    result: dict[str, Any] = {"resources": [res.model_dump() for res in resources]}
    return JSONRPCResponse(jsonrpc="2.0", id=request.id, result=result)


def _handle_resources_read(request: JSONRPCRequest) -> JSONRPCResponse:
    """Handle resources/read method."""
    if not request.params or "uri" not in request.params:
        raise ValueError("Missing resource URI")

    uri = str(request.params["uri"])
    project_id_val = request.params.get("project_id")
    project_id = str(project_id_val) if project_id_val is not None else None

    content = get_resource_content(uri, project_id)
    result: dict[str, Any] = {"contents": [{"uri": uri, "mimeType": "text/plain", "text": content}]}
    return JSONRPCResponse(jsonrpc="2.0", id=request.id, result=result)


def _handle_method_not_found(request: JSONRPCRequest) -> JSONRPCResponse:
    """Handle unknown methods."""
    error: dict[str, Any] = {"code": -32601, "message": f"Method not found: {request.method}"}
    return JSONRPCResponse(jsonrpc="2.0", id=request.id, error=error)


async def _dispatch_jsonrpc(request: JSONRPCRequest, session: Session) -> JSONRPCResponse:
    """Dispatch JSON-RPC request to appropriate handler."""
    method = request.method

    if method == "initialize":
        return _handle_initialize(request)
    if method == "tools/list":
        return _handle_tools_list(request)
    if method == "tools/call":
        return await _handle_tools_call(request, session)
    if method == "resources/list":
        return _handle_resources_list(request)
    if method == "resources/read":
        return _handle_resources_read(request)
    return _handle_method_not_found(request)


def create_mcp_router() -> APIRouter:
    """Create MCP router with endpoints."""
    router = APIRouter()

    @router.get("/")
    def mcp_health() -> dict[str, str]:
        """MCP health endpoint."""
        return {"status": "ok", "service": "mcp-server"}

    @router.post("/")
    async def handle_jsonrpc(
        request: JSONRPCRequest,
        session: Session = Depends(get_session),  # noqa: B008
    ) -> JSONResponse:
        """Handle JSON-RPC 2.0 requests."""
        try:
            response = await _dispatch_jsonrpc(request, session)
        except Exception as e:
            error: dict[str, Any] = {"code": -32603, "message": str(e)}
            response = JSONRPCResponse(jsonrpc="2.0", id=request.id, error=error)

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
