# Agent Permissions Model — UPCP v2

> Scope: `security` / `agents` | Version: 2.0.0

## 1. Overview

UPCP agents are AI entities that work with tasks on behalf of users.
Each agent has its own token, restricted permissions, and must pass audit.

## 2. Agent Roles

| Role                   | Purpose                                |
|------------------------|----------------------------------------|
| `Agent Reader`         | Read-only access to project data      |
| `Agent Contributor`    | Read + write task results             |
| `Agent Builder`        | Contributor + create files/artifacts  |
| `Agent Reviewer`       | Contributor + approve/reject results  |

### 2.1 Agent Builder (default)

Default role when creating an agent.
Full task work: execution, artifact creation, submission for review.

## 3. Permission Matrix

### 3.1 Tasks

| Action                          | Reader | Contributor | Builder | Reviewer |
|---------------------------------|:------:|:-----------:|:-------:|:--------:|
| View tasks                      | ✅     | ✅          | ✅      | ✅       |
| View task details               | ✅     | ✅          | ✅      | ✅       |
| Claim task                      | ❌     | ✅          | ✅      | ✅       |
| Send heartbeat                  | ❌     | ✅          | ✅      | ✅       |
| Submit result                   | ❌     | ✅          | ✅      | ✅       |
| Request clarification           | ❌     | ✅          | ✅      | ✅       |
| Request review                  | ❌     | ✅          | ✅      | ❌       |
| Approve/Reject result           | ❌     | ❌          | ❌      | ✅       |
| Release task                    | ❌     | ✅          | ✅      | ✅       |

### 3.2 Files and Artifacts

| Action                          | Reader | Contributor | Builder | Reviewer |
|---------------------------------|:------:|:-----------:|:-------:|:--------:|
| Read project files              | ✅     | ✅          | ✅      | ✅       |
| Create files                    | ❌     | ❌          | ✅      | ❌       |
| Modify files                    | ❌     | ❌          | ✅      | ❌       |
| Delete files                    | ❌     | ❌          | ❌      | ❌       |
| Upload artifacts                | ❌     | ✅          | ✅      | ✅       |

### 3.3 MCP

| Action                          | Reader | Contributor | Builder | Reviewer |
|---------------------------------|:------:|:-----------:|:-------:|:--------:|
| MCP: read                       | ✅     | ✅          | ✅      | ✅       |
| MCP: call tools                 | ❌     | ✅          | ✅      | ✅       |
| MCP: manage servers             | ❌     | ❌          | ❌      | ❌       |

### 3.4 Administration

| Action                          | Reader | Contributor | Builder | Reviewer |
|---------------------------------|:------:|:-----------:|:-------:|:--------:|
| View audit log (own)            | ✅     | ✅          | ✅      | ✅       |
| View audit log (all)            | ❌     | ❌          | ❌      | ❌       |
| Manage members                  | ❌     | ❌          | ❌      | ❌       |
| Project settings                | ❌     | ❌          | ❌      | ❌       |

## 4. What Agents CAN Do

- Read tasks, specifications, project documentation
- Claim available tasks within their role scope
- Send heartbeat every 30–60 seconds
- Create files and artifacts (Builder+)
- Submit results for review
- Request clarifications from users
- Call permitted MCP tools
- Upload artifacts (screenshots, logs, reports)

## 5. What Agents CANNOT Do

- Modify RBAC permissions
- Manage other agents (except Reviewer approve/reject)
- Access project secrets/credentials
- Delete data (files, tasks, users)
- Access projects beyond their assigned scope
- Create users or manage auth
- Access unredacted audit logs of all agents
- Disable rate limiting or auditing
- Use blocked MCP tools

## 6. Agent Token Management

### 6.1 Creating a Token

```
POST /api/v1/projects/{project_id}/agent-tokens
Body: {
  "name": "agent-builder-01",
  "role": "agent_builder",
  "expires_at": "2026-08-01T00:00:00Z"
}
```

- Token is created once, shown to the client and stored as a hash
- Bound to a specific project (scope restriction)
- Max 20 active tokens per project

### 6.2 Token Format

```
agp_{project_id}_{random_32}
```

- `project_id` — project ID for fast route determination
- `random_32` — 32 characters, cryptographically secure random

### 6.3 Revoking a Token

```
DELETE /api/v1/projects/{project_id}/agent-tokens/{token_id}
```

- Immediate revocation
- Logs: `agent.token.revoked`
- All active agent sessions using this token are terminated

### 6.4 Rotation

- Recommended TTL: 30 days
- On rotation: old token revoked, new token created
- Automatic warning 7 days before expiration

## 7. Scope Restrictions

- An agent works **only** within the project its token is bound to
- Cross-project access is forbidden at the middleware level
- An agent cannot change its token's scope
- Attempting to access another project → `403 Forbidden` + audit event

## 8. Audit Requirements

Every agent action is logged:

| Event                       | Required Fields                                    |
|-----------------------------|---------------------------------------------------|
| `agent.token.created`       | token_id, project_id, role, created_by            |
| `agent.token.revoked`       | token_id, project_id, revoked_by, reason          |
| `agent.task.claimed`        | agent_id, task_id, timestamp                      |
| `agent.task.released`       | agent_id, task_id, reason                         |
| `agent.task.submitted`      | agent_id, task_id, summary                        |
| `agent.task.approved`       | agent_id, task_id, reviewer_id                    |
| `agent.task.rejected`       | agent_id, task_id, reviewer_id, reason            |
| `agent.heartbeat`           | agent_id, task_id, message (optional)             |
| `agent.clarification`       | agent_id, task_id, question                       |
| `agent.file.created`        | agent_id, task_id, file_path                      |
| `agent.file.modified`       | agent_id, task_id, file_path                      |
| `agent.mcp.tool_called`     | agent_id, tool_name, arguments (sanitized)        |
| `agent.scope.denied`        | agent_id, attempted_scope, actual_scope           |

## 9. Rate Limiting for Agents

| Endpoint              | Limit                |
|-----------------------|----------------------|
| General requests      | 500 req/min/token    |
| Heartbeat             | 120 req/min/token    |
| File uploads          | 50 req/min/token     |
| MCP tool calls        | 200 req/min/token    |

On exceed → `429 Too Many Requests` + `agent.rate_limit.exceeded` audit event.
