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
        Tool(
            name="feature_update",
            description="Update an existing feature",
            input_schema=ToolInput(
                properties={
                    "feature_id": {"type": "string"},
                    "name": {"type": "string"},
                    "slug": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                },
                required=["feature_id"],
            ),
        ),
        Tool(
            name="task_update",
            description="Update an existing task",
            input_schema=ToolInput(
                properties={
                    "task_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                    "priority": {"type": "integer"},
                },
                required=["task_id"],
            ),
        ),
        # --- Workflow tools ---
        Tool(
            name="claim_task",
            description="Claim a ready task for an agent",
            input_schema=ToolInput(
                properties={
                    "task_id": {"type": "string"},
                    "agent_id": {"type": "string"},
                    "context_snapshot": {"type": "string"},
                },
                required=["task_id", "agent_id"],
            ),
        ),
        Tool(
            name="release_task",
            description="Release an agent's claim on a task",
            input_schema=ToolInput(
                properties={
                    "task_id": {"type": "string"},
                    "agent_id": {"type": "string"},
                },
                required=["task_id", "agent_id"],
            ),
        ),
        Tool(
            name="heartbeat_task",
            description="Send a heartbeat on a claimed task",
            input_schema=ToolInput(
                properties={
                    "task_id": {"type": "string"},
                    "agent_id": {"type": "string"},
                    "progress_percent": {"type": "integer"},
                    "current_step": {"type": "string"},
                    "next_step": {"type": "string"},
                    "blockers": {"type": "string"},
                    "eta": {"type": "string"},
                },
                required=["task_id", "agent_id", "progress_percent", "current_step", "next_step"],
            ),
        ),
        Tool(
            name="request_clarification",
            description="Request clarification on a task",
            input_schema=ToolInput(
                properties={
                    "task_id": {"type": "string"},
                    "agent_id": {"type": "string"},
                    "question": {"type": "string"},
                    "context": {"type": "string"},
                    "blocking": {"type": "boolean"},
                },
                required=["task_id", "agent_id", "question"],
            ),
        ),
        Tool(
            name="answer_clarification",
            description="Answer a clarification request",
            input_schema=ToolInput(
                properties={
                    "clarification_id": {"type": "string"},
                    "answer": {"type": "string"},
                    "answered_by": {"type": "string"},
                },
                required=["clarification_id", "answer", "answered_by"],
            ),
        ),
        Tool(
            name="submit_task_for_review",
            description="Submit a task for review",
            input_schema=ToolInput(
                properties={
                    "task_id": {"type": "string"},
                    "agent_id": {"type": "string"},
                },
                required=["task_id", "agent_id"],
            ),
        ),
        Tool(
            name="get_agent_inbox",
            description="Get agent inbox events",
            input_schema=ToolInput(
                properties={
                    "agent_id": {"type": "string"},
                    "since": {"type": "string"},
                },
                required=["agent_id"],
            ),
        ),
        Tool(
            name="get_agent_playbook",
            description="Get the agent playbook content",
            input_schema=ToolInput(properties={}),
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
    if isinstance(val, int | float):
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


def _serialize_paginated(
    items: list[dict[str, Any]], total: int, offset: int, limit: int
) -> dict[str, Any]:
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
    feature = service.create(
        project_id=project_id, name=name, slug=slug, description=description, status=status
    )
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
        feature_id=feature_id,
        title=title,
        description=description,
        status=status,
        priority=priority,
    )
    result = _serialize_task(task)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_feature_update(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle feature_update tool."""
    feature_id = _get_str_arg(arguments, "feature_id")
    if not feature_id:
        raise ValueError("feature_id is required")
    fields: dict[str, str | None] = {}
    for key in ("name", "slug", "description", "status"):
        val = arguments.get(key)
        if val is not None:
            fields[key] = str(val)
    service = FeatureService(session)
    feature = service.update(feature_id, **fields)
    result = _serialize_feature(feature)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_task_update(session: Any, arguments: dict[str, object]) -> ToolResult:
    """Handle task_update tool."""
    task_id = _get_str_arg(arguments, "task_id")
    if not task_id:
        raise ValueError("task_id is required")
    fields: dict[str, str | int | None] = {}
    for key in ("title", "description", "status"):
        val = arguments.get(key)
        if val is not None:
            fields[key] = str(val)
    if "priority" in arguments and arguments["priority"] is not None:
        fields["priority"] = _get_int_arg(arguments, "priority", 0)
    service = TaskService(session)
    task = service.update(task_id, **fields)
    result = _serialize_task(task)
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


# ── Workflow handlers ──


def _handle_claim_task(session: Any, arguments: dict[str, object]) -> ToolResult:
    from app.delivery.workflow import WorkflowService

    task_id = _get_str_arg(arguments, "task_id")
    agent_id = _get_str_arg(arguments, "agent_id")
    if not task_id or not agent_id:
        raise ValueError("task_id and agent_id are required")
    svc = WorkflowService(session)
    claim = svc.claim(
        task_id,
        agent_id=agent_id,
        context_snapshot=_get_str_arg(arguments, "context_snapshot") or None,
    )
    result = {
        "id": claim.id,
        "task_id": claim.task_id,
        "agent_id": claim.agent_id,
        "state": claim.state,
        "claimed_at": claim.claimed_at.isoformat() if claim.claimed_at else None,
    }
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_release_task(session: Any, arguments: dict[str, object]) -> ToolResult:
    from app.delivery.workflow import WorkflowService

    task_id = _get_str_arg(arguments, "task_id")
    agent_id = _get_str_arg(arguments, "agent_id")
    if not task_id or not agent_id:
        raise ValueError("task_id and agent_id are required")
    svc = WorkflowService(session)
    svc.release(task_id, agent_id=agent_id)
    return ToolResult(content=[{"type": "text", "text": json.dumps({"ok": True})}])


def _handle_heartbeat_task(session: Any, arguments: dict[str, object]) -> ToolResult:
    from app.delivery.workflow import WorkflowService

    task_id = _get_str_arg(arguments, "task_id")
    agent_id = _get_str_arg(arguments, "agent_id")
    if not task_id or not agent_id:
        raise ValueError("task_id and agent_id are required")
    svc = WorkflowService(session)
    svc.heartbeat(
        task_id,
        agent_id=agent_id,
        progress_percent=_get_int_arg(arguments, "progress_percent", 0),
        current_step=_get_str_arg(arguments, "current_step"),
        next_step=_get_str_arg(arguments, "next_step"),
        blockers=_get_str_arg(arguments, "blockers") or None,
        eta=_get_str_arg(arguments, "eta") or None,
    )
    return ToolResult(content=[{"type": "text", "text": json.dumps({"ok": True})}])


def _handle_request_clarification(session: Any, arguments: dict[str, object]) -> ToolResult:
    from app.delivery.models import ClarificationRequest, Task
    from app.shared.text import new_id

    task_id = _get_str_arg(arguments, "task_id")
    agent_id = _get_str_arg(arguments, "agent_id")
    question = _get_str_arg(arguments, "question")
    if not task_id or not agent_id or not question:
        raise ValueError("task_id, agent_id, and question are required")
    task = session.get(Task, task_id)
    if task is None:
        raise ValueError(f"task '{task_id}' not found")
    blocking = arguments.get("blocking", False) is True
    cr = ClarificationRequest(
        id=new_id(),
        task_id=task_id,
        author_type="agent",
        author_id=agent_id,
        question=question,
        context=_get_str_arg(arguments, "context") or None,
        blocking=blocking,
    )
    session.add(cr)
    if blocking:
        from app.delivery.lifecycle import validate_transition

        validate_transition(task.status, "needs_clarification")
        task.status = "needs_clarification"
    session.flush()
    result = {
        "id": cr.id,
        "task_id": cr.task_id,
        "state": cr.state,
        "question": cr.question,
        "blocking": cr.blocking,
    }
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_answer_clarification(session: Any, arguments: dict[str, object]) -> ToolResult:
    from datetime import UTC, datetime

    from app.delivery.models import ClarificationRequest

    clar_id = _get_str_arg(arguments, "clarification_id")
    answer = _get_str_arg(arguments, "answer")
    answered_by = _get_str_arg(arguments, "answered_by")
    if not clar_id or not answer or not answered_by:
        raise ValueError("clarification_id, answer, and answered_by are required")
    cr = session.query(ClarificationRequest).filter_by(id=clar_id).first()
    if cr is None:
        raise ValueError(f"clarification '{clar_id}' not found")
    if cr.state != "open":
        raise ValueError(f"clarification is '{cr.state}', can only answer 'open' ones")
    cr.state = "answered"
    cr.answer = answer
    cr.answered_by = answered_by
    cr.answered_at = datetime.now(UTC)
    session.flush()
    result = {"id": cr.id, "state": cr.state, "answer": cr.answer}
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_submit_task_for_review(session: Any, arguments: dict[str, object]) -> ToolResult:
    from app.delivery.lifecycle import validate_transition
    from app.delivery.models import Task, TaskClaim

    task_id = _get_str_arg(arguments, "task_id")
    agent_id = _get_str_arg(arguments, "agent_id")
    if not task_id:
        raise ValueError("task_id is required")
    task = session.get(Task, task_id)
    if task is None:
        raise ValueError(f"task '{task_id}' not found")
    if agent_id:
        claim = (
            session.query(TaskClaim)
            .filter_by(task_id=task_id, agent_id=agent_id, state="active")
            .first()
        )
        if claim is None:
            raise ValueError(f"agent '{agent_id}' has no active claim on task '{task_id}'")
    validate_transition(task.status, "ready_for_review")
    task.status = "ready_for_review"
    session.flush()
    result = {"id": task.id, "status": task.status}
    return ToolResult(content=[{"type": "text", "text": json.dumps(result, indent=2)}])


def _handle_get_agent_inbox(session: Any, arguments: dict[str, object]) -> ToolResult:
    # MVP: return empty inbox
    return ToolResult(content=[{"type": "text", "text": json.dumps({"events": []})}])


_PLAYBOOK = """# Agent Playbook

## Task Workflow
1. Claim a ready task
2. Send heartbeats every 30-60s
3. Ask questions if blocked
4. Submit for review when done

## Status Flow
backlog → ready → claimed → in_progress → done
"""


def _handle_get_agent_playbook(session: Any, arguments: dict[str, object]) -> ToolResult:
    return ToolResult(content=[{"type": "text", "text": json.dumps({"content": _PLAYBOOK})}])


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
    "feature_update": _handle_feature_update,
    "task_update": _handle_task_update,
    # Workflow tools
    "claim_task": _handle_claim_task,
    "release_task": _handle_release_task,
    "heartbeat_task": _handle_heartbeat_task,
    "request_clarification": _handle_request_clarification,
    "answer_clarification": _handle_answer_clarification,
    "submit_task_for_review": _handle_submit_task_for_review,
    "get_agent_inbox": _handle_get_agent_inbox,
    "get_agent_playbook": _handle_get_agent_playbook,
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
