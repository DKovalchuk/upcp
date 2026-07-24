"""MCP server implementation."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.mcp.resources import get_resource_content, get_resources
from app.mcp.schemas import (
    JSONRPCRequest,
    JSONRPCResponse,
)
from app.mcp.tools import call_tool, get_tools


def create_mcp_router() -> APIRouter:
    """Create MCP router with endpoints."""
    router = APIRouter()

    @router.get("/")
    def mcp_health() -> dict[str, str]:
        """MCP health endpoint."""
        return {"status": "ok", "service": "mcp-server"}

    @router.post("/")
    async def handle_jsonrpc(request: JSONRPCRequest) -> JSONResponse:
        """Handle JSON-RPC 2.0 requests."""
        from typing import Any, cast

        try:
            response: JSONRPCResponse
            if request.method == "initialize":
                result = cast(dict[str, Any], {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                    },
                    "serverInfo": {
                        "name": "upcp-mcp-server",
                        "version": "1.0.0",
                    },
                })
                response = JSONRPCResponse(jsonrpc="2.0", id=request.id, result=result)
            elif request.method == "tools/list":
                tools = get_tools()
                result = cast(dict[str, Any], {"tools": [tool.model_dump() for tool in tools]})
                response = JSONRPCResponse(jsonrpc="2.0", id=request.id, result=result)
            elif request.method == "tools/call":
                if not request.params or "name" not in request.params:
                    raise ValueError("Missing tool name")
                tool_name = str(request.params["name"])
                arguments = dict(request.params.get("arguments", {}) or {})
                tool_result = await call_tool(tool_name, arguments)
                result = cast(dict[str, Any], tool_result.model_dump())
                response = JSONRPCResponse(jsonrpc="2.0", id=request.id, result=result)
            elif request.method == "resources/list":
                resources = get_resources()
                result = cast(dict[str, Any], {"resources": [res.model_dump() for res in resources]})
                response = JSONRPCResponse(jsonrpc="2.0", id=request.id, result=result)
            elif request.method == "resources/read":
                if not request.params or "uri" not in request.params:
                    raise ValueError("Missing resource URI")
                uri = str(request.params["uri"])
                project_id = str(request.params.get("project_id", "")) if request.params.get("project_id") else None
                content = get_resource_content(uri, project_id)
                result = cast(dict[str, Any], {"contents": [{"uri": uri, "mimeType": "text/plain", "text": content}]})
                response = JSONRPCResponse(jsonrpc="2.0", id=request.id, result=result)
            else:
                error = cast(dict[str, Any], {"code": -32601, "message": f"Method not found: {request.method}"})
                response = JSONRPCResponse(jsonrpc="2.0", id=request.id, error=error)
        except Exception as e:
            error = cast(dict[str, Any], {"code": -32603, "message": str(e)})
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