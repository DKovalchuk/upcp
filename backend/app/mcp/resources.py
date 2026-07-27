"""MCP resource implementations."""

from app.mcp.context_pack import get_context_pack
from app.mcp.schemas import Resource


def get_resources() -> list[Resource]:
    """Get list of available resources."""
    return [
        Resource(
            uri="context_pack://project",
            name="context_pack",
            description="Generate context pack for AI agents",
            mime_type="text/markdown",
        ),
    ]


def get_resource_content(uri: str, project_id: str | None = None) -> str:
    """Get resource content by URI."""
    if uri == "context_pack://project":
        return get_context_pack(project_id)
    else:
        raise ValueError(f"Unknown resource: {uri}")
