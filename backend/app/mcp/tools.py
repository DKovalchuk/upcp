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
        # --- Write tools ---
        Tool(
            name="project_create",
            description="Create a new project",
            input_schema=ToolInput(
                properties={
                    "name": {"type": "string"},
                    "slug": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "default": "active"},
                },
                required=["name"],
            ),
        ),
        Tool(
            name="project_update",
            description="Update an existing project",
            input_schema=ToolInput(
                properties={
                    "project_id": {"type": "string"},
                    "name": {"type": "string"},
                    "slug": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                },
                required=["project_id"],
            ),
        ),
        Tool(
            name="feature_create",
            description="Create a new feature in a project",
            input_schema=ToolInput(
                properties={
                    "project_id": {"type": "string"},
                    "name": {"type": "string"},
                    "slug": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "default": "backlog"},
                },
                required=["project_id", "name"],
            ),
        ),
        Tool(
            name="task_create",
            description="Create a new task in a feature",
            input_schema=ToolInput(
                properties={
                    "feature_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "default": "backlog"},
                    "priority": {"type": "integer", "default": 0},
                },
                required=["feature_id", "title"],
            ),
        ),
    ]


MAX_LIMIT = 100
MIN_OFFSET = 0


def _get_int_arg(arguments: dict[str, object], key: str, default: int) -> int:
    """Extract integer from arguments with type-aware conversion.

    Handles bool, int, float, and string types.
    Raises ValueError for empty strings or non-numeric strings.
    """
    val = arguments.get(key)
    if val is None:
        return default
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip()
    if not s:
        raise ValueError(f"{key}: empty string is not a valid integer")
    try:
        return int(s)
    except (ValueError, TypeError) as err:
        raise ValueError(f"{key}: '{s}' is not a valid integer") from err


def _clamped_int(val: int, min_val: int, max_val: int) -> int:
    """Clamp an integer to [min_val, max_val]."""
    return max(min_val, min(max_val, val))


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
        "priority": int(t.priority) if t.priority is not None else None,
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
    offset = _clamped_int(_get_int_arg(arguments, "offset", 0), MIN_OFFSET, MAX_LIMIT)
    limit = _clamped_int(_get_int_arg(arguments, "limit", 20), MIN_OFFSET, MAX_LIMIT)
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
    """Handle task_list tool — lists tasks for a project (via features)."""
    project_id = _get_str_arg(arguments, "project_id")
    if not project_id:
        raise ValueError("project_id is required")
    service = TaskService(session)
    offset = _clamped_int(_get_int_arg(arguments, "offset", 0), MIN_OFFSET, MAX_LIMIT)
    limit = _clamped_int(_get_int_arg(arguments, "limit", 20), MIN_OFFSET, MAX_LIMIT)
    tasks, total = service.list_tasks_by_project(project_id, offset=offset, limit=limit)
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
    offset = _clamped_int(_get_int_arg(arguments, "offset", 0), MIN_OFFSET, MAX_LIMIT)
    limit = _clamped_int(_get_int_arg(arguments, "limit", 20), MIN_OFFSET, MAX_LIMIT)
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


# --- Write tool handlers ---


def _handle_project_create(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle project_create tool."""
    name = _get_str_arg(arguments, "name")
    if not name:
        raise ValueError("name is required")
    slug = _get_str_arg(arguments, "slug") or None
    description = _get_str_arg(arguments, "description") or None
    status = _get_str_arg(arguments, "status", "active") or "active"
    service = ProjectService(session)
    project = service.create(name=name, slug=slug, description=description, status=status)
    result = _serialize_project(project)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_project_update(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle project_update tool."""
    project_id = _get_str_arg(arguments, "project_id")
    if not project_id:
        raise ValueError("project_id is required")
    fields: dict[str, str | None] = {}
    for key in ("name", "slug", "description", "status"):
        val = arguments.get(key)
        if val is not None:
            fields[key] = str(val)
    service = ProjectService(session)
    project = service.update(project_id, **fields)
    result = _serialize_project(project)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_feature_create(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle feature_create tool."""
    project_id = _get_str_arg(arguments, "project_id")
    if not project_id:
        raise ValueError("project_id is required")
    name = _get_str_arg(arguments, "name")
    if not name:
        raise ValueError("name is required")
    slug = _get_str_arg(arguments, "slug") or None
    description = _get_str_arg(arguments, "description") or None
    status = _get_str_arg(arguments, "status", "backlog") or "backlog"
    service = FeatureService(session)
    feature = service.create(project_id=project_id, name=name, slug=slug, description=description, status=status)
    result = _serialize_feature(feature)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_task_create(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle task_create tool."""
    feature_id = _get_str_arg(arguments, "feature_id")
    if not feature_id:
        raise ValueError("feature_id is required")
    title = _get_str_arg(arguments, "title")
    if not title:
        raise ValueError("title is required")
    description = _get_str_arg(arguments, "description") or None
    status = _get_str_arg(arguments, "status", "backlog") or "backlog"
    priority = _get_int_arg(arguments, "priority", 0)
    # Validate feature exists before creating task
    feature_svc = FeatureService(session)
    feature_svc.get(feature_id)
    service = TaskService(session)
    task = service.create(
        feature_id=feature_id, title=title, description=description,
        status=status, priority=priority,
    )
    result = _serialize_task(task)
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
    # Write tools
    "project_create": _handle_project_create,
    "project_update": _handle_project_update,
    "feature_create": _handle_feature_create,
    "task_create": _handle_task_create,
}


async def call_tool(
    name: str,
    arguments: dict[str, object],
    session: Any | None = None,
) -> ToolResult:
    """Call a tool by name using dispatch table.

    If *session* is provided it is used directly (FastAPI DI).
    Otherwise a new SessionLocal is created for backward compatibility.
    """
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")

    own_session = session is None
    sess = session if session is not None else SessionLocal()
    try:
        return handler(sess, arguments)
    except Exception as e:
        content: list[dict[str, object]] = [{"type": "text", "text": f"Error: {str(e)}"}]
        return ToolResult(content=content, is_error=True)
    finally:
        if own_session:
            sess.close()
