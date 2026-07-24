"""MCP schemas for JSON-RPC requests and responses."""
from pydantic import BaseModel, Field


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request."""
    jsonrpc: str = "2.0"
    id: int | str
    method: str
    params: dict[str, object] | None = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response."""
    jsonrpc: str = "2.0"
    id: int | str
    result: dict[str, object] | None = None
    error: dict[str, object] | None = None


class ToolInput(BaseModel):
    """Input schema for a tool."""
    type: str = "object"
    properties: dict[str, object] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class Tool(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    input_schema: ToolInput = Field(default_factory=ToolInput)


class ToolCall(BaseModel):
    """Tool call request."""
    name: str
    arguments: dict[str, object] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Tool call result."""
    content: list[dict[str, object]] = Field(default_factory=list)
    is_error: bool = False


class Resource(BaseModel):
    """MCP resource definition."""
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"