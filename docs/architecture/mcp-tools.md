# MCP Tools — UPCP v2

## Overview

UPCP provides AI agents access through the Model Context Protocol (MCP). All MCP tools are divided into three categories: **read** (data retrieval), **write** (modification), and **admin** (management). Access permissions are determined by the agent's scope.

---

## Authentication

Agents authenticate via `AgentToken`, passed in the MCP handshake. The token determines:
- Agent's organization
- Scope (allowed operations, projects)
- Limits (max_tasks, heartbeat_interval)

---

## Read Tools

### `whoami`

Returns information about the current agent and its capabilities.

```
→ {}
← {
    "agent_id": "01934b2a-...",
    "name": "claude-code-agent",
    "agent_type": "claude",
    "organization_id": "01934b1f-...",
    "capabilities": ["code_review", "implementation"],
    "assigned_projects": ["01934b2c-...", "01934b2d-..."]
}
```

### `get_capabilities`

Returns the full list of available operations for the current agent.

```
→ {}
← {
    "allowed_operations": ["task.read", "task.write", "evidence.create"],
    "max_tasks": 3,
    "heartbeat_interval_sec": 30
}
```

### `get_agent_playbook`

Returns the playbook/instructions for the agent in the project context.

```
→ { "project_id": "01934b2c-..." }
← {
    "project_id": "01934b2c-...",
    "guidelines": "...",
    "conventions": "...",
    "forbidden_patterns": ["..."],
    "required_patterns": ["..."]
}
```

### `list_projects`

List of projects assigned to the agent.

```
→ { "offset": 0, "limit": 20 }
← {
    "data": [
        {
            "id": "01934b2c-...",
            "name": "UPCP",
            "slug": "upcp",
            "status": "active"
        }
    ],
    "meta": { "total": 2, "offset": 0, "limit": 20 }
}
```

### `get_project`

Project details with settings.

```
→ { "project_id": "01934b2c-..." }
← {
    "id": "01934b2c-...",
    "name": "UPCP",
    "description": "...",
    "settings": { "review_policy": "agent_then_human" },
    "stats": { "tasks_total": 42, "tasks_done": 18 }
}
```

### `list_components`

Project components.

```
→ { "project_id": "01934b2c-...", "offset": 0, "limit": 50 }
← { "data": [...], "meta": {...} }
```

### `list_modules`

Component modules.

```
→ { "component_id": "01934b30-...", "offset": 0, "limit": 50 }
← { "data": [...], "meta": {...} }
```

### `list_features`

Module or project features.

```
→ {
    "project_id": "01934b2c-...",
    "module_id": null,
    "filter": { "status": "ready" },
    "offset": 0, "limit": 20
}
← { "data": [...], "meta": {...} }
```

### `list_tasks`

Tasks with filtering. The primary tool for finding work.

```
→ {
    "project_id": "01934b2c-...",
    "filter": {
        "state": "ready",
        "priority": "high"
    },
    "sort": "-priority,created_at",
    "offset": 0, "limit": 20
}
← { "data": [...], "meta": {...} }
```

### `get_task`

Full task information with relationships.

```
→ { "task_id": "01934b35-..." }
← {
    "id": "01934b35-...",
    "title": "Implement auth middleware",
    "description": "...",
    "acceptance_criteria": "...",
    "state": "in_progress",
    "priority": "high",
    "feature": { "id": "...", "title": "..." },
    "module": { "id": "...", "name": "..." },
    "component": { "id": "...", "name": "..." },
    "project": { "id": "...", "name": "..." },
    "subtasks": [...],
    "evidence_count": 3,
    "review_rounds": [...],
    "clarification_requests": [...]
}
```

### `get_context_pack`

Context package for a task — all information needed by the agent to work.

```
→ { "task_id": "01934b35-..." }
← {
    "task": { ... },
    "project_guidelines": "...",
    "component_context": "...",
    "related_tasks": [...],
    "git_branch": "feature/auth-middleware",
    "recent_commits": [...]
}
```

### `get_agent_inbox`

Incoming messages for the agent: clarification answers, notifications.

```
→ { "project_id": null, "unreadOnly": true }
← {
    "data": [
        {
            "type": "clarification_answer",
            "task_id": "01934b35-...",
            "message": "...",
            "created_at": "2025-07-27T10:00:00Z"
        }
    ],
    "meta": { "total": 1 }
}
```

### `list_evidence`

Evidence for a task.

```
→ { "task_id": "01934b35-...", "offset": 0, "limit": 20 }
← { "data": [...], "meta": {...} }
```

### `list_review_rounds`

Review rounds for a task.

```
→ { "task_id": "01934b35-..." }
← {
    "data": [
        {
            "id": "...",
            "round_number": 1,
            "status": "completed",
            "verdict": "approved",
            "findings": [...]
        }
    ]
}
```

---

## Write Tools

### `create_component`

```
→ {
    "project_id": "01934b2c-...",
    "name": "Backend API",
    "description": "FastAPI application"
}
← { "data": { "id": "...", "name": "Backend API", ... } }
```

### `update_component`

```
→ {
    "component_id": "01934b30-...",
    "name": "Backend API v2",
    "description": "Updated description"
}
← { "data": { ... } }
```

### `create_module`

```
→ {
    "component_id": "01934b30-...",
    "name": "Authentication",
    "description": "Auth module"
}
← { "data": { ... } }
```

### `update_module`

```
→ { "module_id": "...", "name": "Auth & RBAC" }
← { "data": { ... } }
```

### `create_feature`

```
→ {
    "module_id": "...",
    "title": "JWT Authentication",
    "description": "...",
    "priority": "high"
}
← { "data": { ... } }
```

### `update_feature`

```
→ { "feature_id": "...", "status": "ready", "priority": "critical" }
← { "data": { ... } }
```

### `create_task`

```
→ {
    "feature_id": "...",
    "title": "Implement login endpoint",
    "description": "...",
    "acceptance_criteria": "...",
    "priority": "high",
    "estimated_effort": "m",
    "review_policy": "agent_then_human"
}
← { "data": { ... } }
```

### `update_task`

```
→ {
    "task_id": "...",
    "title": "Updated title",
    "description": "..."
}
← { "data": { ... } }
```

**Constraints:** You cannot change `state` directly (use state machine tools instead).

### `create_subtask`

```
→ { "task_id": "...", "title": "Write unit tests" }
← { "data": { ... } }
```

### `claim_task`

Atomic task claim. If the task is already claimed — an error is returned.

```
→ { "task_id": "..." }
← {
    "data": {
        "claim_id": "...",
        "task_id": "...",
        "agent_id": "...",
        "claimed_at": "...",
        "expires_at": "..."
    }
}
```

**Errors:**
- `409 TASK_ALREADY_CLAIMED` — task already claimed by another agent
- `422 TASK_NOT_CLAIMABLE` — task is not in the `ready` state

### `release_task`

Release a task (agent cannot continue).

```
→ { "task_id": "...", "reason": "Need more context" }
← { "data": { "released": true } }
```

### `heartbeat_task`

Periodic liveness signal. Required every 30-60 seconds.

```
→ { "task_id": "...", "message": "Running tests..." }
← { "data": { "received_at": "..." } }
```

### `add_task_note`

Add a note to a task.

```
→ { "task_id": "...", "note": "Found edge case in auth flow..." }
← { "data": { "id": "...", "created_at": "..." } }
```

### `request_clarification`

Request clarification from the project owner.

```
→ {
    "task_id": "...",
    "question": "Should the login endpoint support OAuth2 or only email/password?"
}
← { "data": { "clarification_id": "...", "status": "open" } }
```

### `answer_clarification`

Answer a clarification (for owner via MCP or UI).

```
→ {
    "clarification_id": "...",
    "answer": "Only email/password for MVP. OAuth2 will be a separate task."
}
← { "data": { "status": "answered" } }
```

### `attach_evidence`

Attach evidence to a task.

```
→ {
    "task_id": "...",
    "evidence_type": "test_output",
    "title": "Unit test results",
    "content": "42 passed, 0 failed...",
    "metadata": { "test_framework": "pytest" }
}
← { "data": { "id": "...", "created_at": "..." } }
```

### `submit_task_for_review`

Submit a task for review. Changes state to `ready_for_review`.

```
→ {
    "task_id": "...",
    "summary": "Implemented login endpoint with JWT. All tests pass."
}
← { "data": { "state": "ready_for_review", "review_round_id": "..." } }
```

### `request_agent_review`

Request a review from another agent (if policy allows).

```
→ {
    "task_id": "...",
    "reviewer_agent_id": "...",
    "focus": "Security review of auth implementation"
}
← { "data": { "review_round_id": "..." } }
```

### `submit_review_verdict`

Submit a review verdict (for agent reviewers).

```
→ {
    "review_round_id": "...",
    "verdict": "approved",
    "summary": "LGTM. Clean implementation, good test coverage.",
    "findings": [
        {
            "severity": "info",
            "category": "style",
            "description": "Consider extracting token generation to a service",
            "file_path": "src/auth/jwt.py",
            "line_number": 42
        }
    ]
}
← { "data": { "status": "completed", "verdict": "approved" } }
```

---

## Admin Tools

### `create_agent`

```
→ {
    "name": "claude-code-reviewer",
    "agent_type": "claude",
    "description": "Code review specialist",
    "capabilities": ["code_review"],
    "scope": {
        "allowed_operations": ["task.read", "review.*"],
        "max_tasks": 5
    },
    "project_ids": ["01934b2c-..."]
}
← { "data": { "id": "...", "token": "mcp_...", "token_plaintext": "..." } }
```

**Important:** `token_plaintext` is returned ONLY upon creation.

### `revoke_agent_token`

```
→ { "agent_id": "...", "token_id": "..." }
← { "data": { "revoked": true } }
```

### `manage_roles`

```
→ {
    "action": "assign",
    "user_id": "...",
    "project_id": "...",
    "role": "member"
}
← { "data": { "assigned": true } }
```

### `manage_project_members`

```
→ {
    "action": "add",
    "project_id": "...",
    "agent_id": "...",
    "role": "contributor"
}
← { "data": { "added": true } }
```

### `manage_settings`

```
→ {
    "project_id": "...",
    "settings": {
        "review_policy": "agent_then_human",
        "heartbeat_timeout_sec": 120,
        "auto_unclaim_after_sec": 3600
    }
}
← { "data": { "updated": true } }
```

---

## Scope and Permissions

### Operations

| Operation | Description | Read Tools | Write Tools | Admin Tools |
|-----------|-------------|------------|-------------|-------------|
| `project.read` | Read projects | ✅ | — | — |
| `task.read` | Read tasks | ✅ | — | — |
| `task.write` | Create/claim tasks | ✅ | ✅ | — |
| `evidence.create` | Create evidence | ✅ | ✅ | — |
| `review.submit` | Submit for review | ✅ | ✅ | — |
| `review.review` | Conduct review | ✅ | ✅ | — |
| `clarification.*` | Clarification flow | ✅ | ✅ | — |
| `structure.write` | CRUD components/modules | ✅ | ✅ | — |
| `agent.manage` | Manage agents | ✅ | ✅ | ✅ |
| `admin.*` | Administration | ✅ | ✅ | ✅ |

### Rules

1. An agent can only work with assigned projects
2. Claim is only possible when state = `ready`
3. Heartbeat is mandatory, otherwise the claim expires
4. Clarification pauses the task
5. Evidence is bound to the current claim
6. Review submit is only possible from the `in_progress` state
