"""MCP tool implementations."""
import json
from collections.abc import Callable
from typing import Any

from app.delivery.service import FeatureService, TaskService
from app.mcp.schemas import Tool, ToolInput, ToolResult
from app.projects.service import ProjectService
from app.shared.database import SessionLocal


def get_tools() -> list[Tool]:
    """Get list of available tools."""
    return [
        Tool(
            name="project_list",
            description="List all projects with pagination",
            input_schema=ToolInput(
                properties={
                    "offset": {"type": "integer", "default": 0},
                    "limit": {"type": "integer", "default": 20},
                },
            ),
        ),
        Tool(
            name="project_get",
            description="Get project by ID",
            input_schema=ToolInput(
                properties={
                    "project_id": {"type": "string"},
                },
                required=["project_id"],
            ),
        ),
        Tool(
            name="task_list",
            description="List tasks for a project",
            input_schema=ToolInput(
                properties={
                    "project_id": {"type": "string"},
                    "offset": {"type": "integer", "default": 0},
                    "limit": {"type": "integer", "default": 20},
                },
                required=["project_id"],
            ),
        ),
        Tool(
            name="task_get",
            description="Get task by ID",
            input_schema=ToolInput(
                properties={
                    "task_id": {"type": "string"},
                },
                required=["task_id"],
            ),
        ),
        Tool(
            name="feature_list",
            description="List features for a project",
            input_schema=ToolInput(
                properties={
                    "project_id": {"type": "string"},
                    "offset": {"type": "integer", "default": 0},
                    "limit": {"type": "integer", "default": 20},
                },
                required=["project_id"],
            ),
        ),
        Tool(
            name="feature_get",
            description="Get feature by ID",
            input_schema=ToolInput(
                properties={
                    "feature_id": {"type": "string"},
                },
                required=["feature_id"],
            ),
        ),
    ]


def _get_int_arg(arguments: dict[str, object], key: str, default: int) -> int:
    """Extract integer from arguments, handling object type."""
    val = arguments.get(key)
    if val is None:
        return default
    try:
        return int(str(val) or str(default))
    except (ValueError, TypeError):
        return default


def _get_str_arg(arguments: dict[str, object], key: str, default: str = "") -> str:
    """Extract string from arguments, handling object type."""
    val = arguments.get(key)
    if val is None:
        return default
    return str(val)


def _serialize_paginated(items: list[dict[str, Any]], total: int, offset: int, limit: int) -> dict[str, Any]:
    """Serialize paginated result."""
    return {"items": items, "total": total, "offset": offset, "limit": limit}


def _serialize_project(p: Any) -> dict[str, Any]:
    """Serialize a project."""
    return {
        "id": p.id,
        "name": p.name,
        "slug": p.slug,
        "description": p.description,
        "status": p.status,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


def _serialize_task(t: Any) -> dict[str, Any]:
    """Serialize a task."""
    return {
        "id": t.id,
        "feature_id": t.feature_id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": int(str(t.priority)),
        "assignee_type": t.assignee_type,
        "assignee_id": t.assignee_id,
        "component_id": t.component_id,
        "module_id": t.module_id,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
    }


def _serialize_feature(f: Any) -> dict[str, Any]:
    """Serialize a feature."""
    return {
        "id": f.id,
        "project_id": f.project_id,
        "name": f.name,
        "slug": f.slug,
        "description": f.description,
        "status": f.status,
        "component_id": f.component_id,
        "created_at": f.created_at.isoformat(),
        "updated_at": f.updated_at.isoformat(),
    }


def _handle_project_list(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle project_list tool."""
    service = ProjectService(session)
    offset = _get_int_arg(arguments, "offset", 0)
    limit = _get_int_arg(arguments, "limit", 20)
    projects, total = service.list_projects(offset=offset, limit=limit)
    items = [_serialize_project(p) for p in projects]
    result = _serialize_paginated(items, total, offset, limit)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_project_get(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle project_get tool."""
    project_id = _get_str_arg(arguments, "project_id")
    if not project_id:
        raise ValueError("project_id is required")
    service = ProjectService(session)
    project = service.get(project_id)
    result = _serialize_project(project)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_task_list(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle task_list tool (using project_id as feature_id for simplicity)."""
    feature_id = _get_str_arg(arguments, "project_id")
    if not feature_id:
        raise ValueError("project_id (feature_id) is required")
    service = TaskService(session)
    offset = _get_int_arg(arguments, "offset", 0)
    limit = _get_int_arg(arguments, "limit", 20)
    tasks, total = service.list_tasks(feature_id, offset=offset, limit=limit)
    items = [_serialize_task(t) for t in tasks]
    result = _serialize_paginated(items, total, offset, limit)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_task_get(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle task_get tool."""
    task_id = _get_str_arg(arguments, "task_id")
    if not task_id:
        raise ValueError("task_id is required")
    service = TaskService(session)
    task = service.get(task_id)
    result = _serialize_task(task)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_feature_list(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle feature_list tool."""
    project_id = _get_str_arg(arguments, "project_id")
    if not project_id:
        raise ValueError("project_id is required")
    service = FeatureService(session)
    offset = _get_int_arg(arguments, "offset", 0)
    limit = _get_int_arg(arguments, "limit", 20)
    features, total = service.list_features(project_id, offset=offset, limit=limit)
    items = [_serialize_feature(f) for f in features]
    result = _serialize_paginated(items, total, offset, limit)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_feature_get(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle feature_get tool."""
    feature_id = _get_str_arg(arguments, "feature_id")
    if not feature_id:
        raise ValueError("feature_id is required")
    service = FeatureService(session)
    feature = service.get(feature_id)
    result = _serialize_feature(feature)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


# Dispatch table mapping tool names to handler functions
HandlerFn = Callable[[Any, dict[str, object]], ToolResult]
TOOL_HANDLERS: dict[str, HandlerFn] = {
    "project_list": _handle_project_list,
    "project_get": _handle_project_get,
    "task_list": _handle_task_list,
    "task_get": _handle_task_get,
    "feature_list": _handle_feature_list,
    "feature_get": _handle_feature_get,
}


async def call_tool(name: str, arguments: dict[str, object]) -> ToolResult:
    """Call a tool by name using dispatch table."""
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")

    session = SessionLocal()
    try:
        return handler(session, arguments)
    except Exception as e:
        content: list[dict[str, object]] = [{"type": "text", "text": f"Error: {str(e)}"}]
        return ToolResult(content=content, is_error=True)
    finally:
        session.close()
