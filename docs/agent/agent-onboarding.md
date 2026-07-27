# Agent Onboarding

Guide to registering and setting up an AI agent in UPCP.

---

## 1. Overview

An agent is a software participant in the project with a profile, token, scope, and assignments. Interaction: MCP, REST API, CLI.

### Roles

| Role           | Description               | Operations                           |
|----------------|---------------------------|--------------------------------------|
| `reader`       | Read-only                 | View tasks, context pack            |
| `contributor`  | Read + write              | Claim, heartbeat, evidence, clarification |
| `builder`      | Full write access         | Task CRUD, features, evidence        |
| `reviewer`     | Review                    | Findings + verdicts                  |

---

## 2. Creating a Profile

### UI
Agent Center → New Agent → Name, Type, Description, Capabilities → Create.

### REST API

```http
POST /api/v1/agents
{ "name": "claude-opus-reviewer", "type": "llm",
  "description": "Code review agent", "capabilities": ["code_review"] }
// → { "id": "agt_...", "name": "...", "status": "active", ... }
```

### CLI

```bash
upcp agent create --name "claude-opus-reviewer" --type llm --capabilities code_review
```

---

## 3. Generating a Token

The token is shown **once**. Save it immediately.

### UI
Agent Profile → Tokens → Generate Token → select scope → copy.

### REST API

```http
POST /api/v1/agents/{agent_id}/tokens
{ "name": "primary", "scopes": ["projects:read", "tasks:write", "evidence:write"] }
// → { "id": "tok_...", "token": "upcp_agt_...", "scopes": [...], ... }
```

### Format

```
upcp_agt_<base62-random-48>
```

---

## 4. Configuring Scope

| Scope              | Description                      |
|---------------------|----------------------------------|
| `projects:read/write` | Projects                      |
| `structure:read/write` | Components, modules           |
| `delivery:read/write` | Features, tasks               |
| `quality:read/write`  | AC, DoD                      |
| `evidence:read/write` | Evidence                    |
| `review:read/write`   | Review rounds, findings      |
| `audit:read`           | Audit events                 |
| `git:read`             | Git data                     |

### Minimum Scope per Role

| Role           | Scope                                                       |
|----------------|-------------------------------------------------------------|
| `reader`       | `projects:read`, `delivery:read`, `quality:read`           |
| `contributor`  | + `delivery:write`, `evidence:write`                       |
| `builder`      | + `structure:write`, `quality:write`                       |
| `reviewer`     | reader + `review:read/write`, `evidence:read`              |

---

## 5. Project Assignment

An agent works only with assigned projects.

### UI
Agent Center → Assignments → Assign to Project → select project and role.

### REST API

```http
POST /api/v1/agents/{agent_id}/assignments
{ "project_id": "proj_abc123", "role": "contributor" }
```

### CLI

```bash
upcp agent assign --agent-id agt_... --project-id proj_... --role contributor
```

---

## 6. First Task Claim

### MCP Client (HTTP)

```json
{
  "mcpServers": {
    "upcp": {
      "url": "http://localhost:38080/mcp/",
      "headers": { "X-Agent-Token": "upcp_agt_..." }
    }
  }
}
```

### MCP Client (stdio bridge)

```json
{
  "mcpServers": {
    "upcp": {
      "command": "python",
      "args": ["mcp-setup/mcp-bridge.py"],
      "env": { "UPCP_MCP_URL": "http://localhost:38080/mcp/", "UPCP_AGENT_TOKEN": "upcp_agt_..." }
    }
  }
}
```

### Connect and Claim

```
tools/call → whoami                              # verify connection
tools/call → get_context_pack { project_id, tier: "standard" }
tools/call → claim_task { task_id, idempotency_key: "<uuid>" }
```

### CLI

```bash
upcp agent whoami                    # verify
upcp agent inbox                     # incoming
upcp task list proj_... --status ready
upcp task claim task_xyz789
```

---

## 7. Smoke Test

```bash
curl http://localhost:38080/api/v1/health                        # health
curl -H "X-Agent-Token: $TOKEN" .../api/v1/agents/whoami         # token
upcp context-pack proj_... --tier minimal                         # context
upcp task list proj_... --limit 5                                 # tasks
```

---

## 8. Troubleshooting

| Problem              | Solution                                  |
|----------------------|-------------------------------------------|
| `UNAUTHENTICATED`    | Check `X-Agent-Token`                     |
| `FORBIDDEN`          | Check scope                               |
| `AGENT_TOKEN_REVOKED`| Reissue the token                         |
| `AGENT_SCOPE_INSUFFICIENT` | Add the required scope              |
| Cannot see project   | Check assignment via `whoami`             |
| MCP not responding   | Check `/api/v1/health`                    |
| Stdio bridge crashes | Check environment variables               |
