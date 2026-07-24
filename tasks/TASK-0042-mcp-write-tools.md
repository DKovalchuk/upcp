# TASK-0042: MCP Write Tools (CRUD)

Spec: SPEC-0011 (MCP)
Status: pending
Priority: 1
Model: routine
Milestone: M5

## Goal

Add write tools to MCP server: project_create, project_update, feature_create, task_create. Currently all 6 MCP tools are read-only.

## Current MCP Tools

```text
project_list    (read)
project_get     (read)
feature_list    (read)
feature_get     (read)
task_list       (read)
task_get        (read)
```

## Tools to Add

```text
project_create  (write) — create project with name, slug, description
project_update  (write) — update project status, name, description
feature_create  (write) — create feature in project
task_create     (write) — create task in feature
```

## Implementation

### 1. Add tool schemas in `backend/app/mcp/tools.py`

```python
Tool(
    name="project_create",
    description="Create a new project",
    input_schema=ToolInput(
        properties={
            "name": {"type": "string"},
            "slug": {"type": "string"},
            "description": {"type": "string"},
        },
        required=["name"],
    ),
),
Tool(
    name="project_update",
    description="Update a project",
    input_schema=ToolInput(
        properties={
            "project_id": {"type": "string"},
            "name": {"type": "string"},
            "status": {"type": "string"},
            "description": {"type": "string"},
        },
        required=["project_id"],
    ),
),
Tool(
    name="feature_create",
    description="Create a feature in a project",
    input_schema=ToolInput(
        properties={
            "project_id": {"type": "string"},
            "name": {"type": "string"},
            "slug": {"type": "string"},
            "description": {"type": "string"},
        },
        required=["project_id", "name"],
    ),
),
Tool(
    name="task_create",
    description="Create a task in a feature",
    input_schema=ToolInput(
        properties={
            "feature_id": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "status": {"type": "string"},
            "priority": {"type": "integer"},
        },
        required=["feature_id", "title"],
    ),
),
```

### 2. Add handler functions

```python
def _handle_project_create(session, arguments):
    name = _get_str_arg(arguments, "name")
    if not name:
        raise ValueError("name is required")
    slug = _get_str_arg(arguments, "slug")
    description = _get_str_arg(arguments, "description")
    service = ProjectService(session)
    project = service.create(name=name, slug=slug, description=description)
    return ToolResult(content=[{"type": "text", "text": json.dumps(_serialize_project(project), indent=2)}])
```

### 3. Add to TOOL_HANDLERS dispatch table

### 4. Write tests for each new tool

## TDD Steps

1. Write tests for project_create via MCP
2. Write tests for project_update via MCP
3. Write tests for feature_create via MCP
4. Write tests for task_create via MCP
5. Implement handlers
6. Verify all tests pass
7. Test manually with curl

## Acceptance Criteria

- `project_create` creates project in database
- `project_update` updates project fields
- `feature_create` creates feature in project
- `task_create` creates task in feature
- All existing MCP tests still pass
- New tests for each write tool
- `make test` passes

## DoD

- 4 new MCP write tools implemented;
- tests pass;
- manual verification with curl;
- task file updated.
