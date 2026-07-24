"""MCP tool implementations."""
import json

from app.delivery.service import TaskService
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


async def call_tool(name: str, arguments: dict[str, object]) -> ToolResult:
    """Call a tool by name."""
    session = SessionLocal()
    try:
        if name == "project_list":
            service = ProjectService(session)
            offset = int(arguments.get("offset", 0))
            limit = int(arguments.get("limit", 20))
            projects, total = service.list_projects(offset=offset, limit=limit)
            items = [
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "description": p.description,
                    "status": p.status,
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat(),
                }
                for p in projects
            ]
            result = {"items": items, "total": total, "offset": offset, "limit": limit}
            content: list[dict[str, object]] = [{"type": "text", "text": json.dumps(result, indent=2)}]
            return ToolResult(content=content)
        elif name == "project_get":
            project_id = str(arguments.get("project_id", ""))
            if not project_id:
                raise ValueError("project_id is required")
            service = ProjectService(session)
            project = service.get(project_id)
            result = {
                "id": project.id,
                "name": project.name,
                "slug": project.slug,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            }
            content = [{"type": "text", "text": json.dumps(result, indent=2)}]
            return ToolResult(content=content)
        elif name == "task_list":
            feature_id = str(arguments.get("project_id", ""))  # Using project_id as feature_id for simplicity
            if not feature_id:
                raise ValueError("project_id (feature_id) is required")
            task_service = TaskService(session)
            offset = int(arguments.get("offset", 0))
            limit = int(arguments.get("limit", 20))
            tasks, total = task_service.list_tasks(feature_id, offset=offset, limit=limit)
            items = [
                {
                    "id": t.id,
                    "feature_id": t.feature_id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority,
                    "assignee_type": t.assignee_type,
                    "assignee_id": t.assignee_id,
                    "component_id": t.component_id,
                    "module_id": t.module_id,
                    "created_at": t.created_at.isoformat(),
                    "updated_at": t.updated_at.isoformat(),
                }
                for t in tasks
            ]
            result = {"items": items, "total": total, "offset": offset, "limit": limit}
            content = [{"type": "text", "text": json.dumps(result, indent=2)}]
            return ToolResult(content=content)
        elif name == "task_get":
            task_id = str(arguments.get("task_id", ""))
            if not task_id:
                raise ValueError("task_id is required")
            task_service = TaskService(session)
            task = task_service.get(task_id)
            result = {
                "id": task.id,
                "feature_id": task.feature_id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "assignee_type": task.assignee_type,
                "assignee_id": task.assignee_id,
                "component_id": task.component_id,
                "module_id": task.module_id,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }
            content = [{"type": "text", "text": json.dumps(result, indent=2)}]
            return ToolResult(content=content)
        elif name == "feature_list":
            project_id = str(arguments.get("project_id", ""))
            if not project_id:
                raise ValueError("project_id is required")
            from app.delivery.service import FeatureService
            feature_service = FeatureService(session)
            offset = int(arguments.get("offset", 0))
            limit = int(arguments.get("limit", 20))
            features, total = feature_service.list_features(project_id, offset=offset, limit=limit)
            items = [
                {
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
                for f in features
            ]
            result = {"items": items, "total": total, "offset": offset, "limit": limit}
            content = [{"type": "text", "text": json.dumps(result, indent=2)}]
            return ToolResult(content=content)
        elif name == "feature_get":
            feature_id = str(arguments.get("feature_id", ""))
            if not feature_id:
                raise ValueError("feature_id is required")
            from app.delivery.service import FeatureService
            feature_service = FeatureService(session)
            feature = feature_service.get(feature_id)
            result = {
                "id": feature.id,
                "project_id": feature.project_id,
                "name": feature.name,
                "slug": feature.slug,
                "description": feature.description,
                "status": feature.status,
                "component_id": feature.component_id,
                "created_at": feature.created_at.isoformat(),
                "updated_at": feature.updated_at.isoformat(),
            }
            content = [{"type": "text", "text": json.dumps(result, indent=2)}]
            return ToolResult(content=content)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        content = [{"type": "text", "text": f"Error: {str(e)}"}]
        return ToolResult(content=content, is_error=True)
    finally:
        session.close()