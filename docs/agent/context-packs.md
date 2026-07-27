# Context Packs

Documentation on the UPCP context pack system for AI agents.

---

## 1. Overview

A context pack is a structured markdown document containing relevant project information for an agent. It is generated on the fly from the database and provided via an MCP resource or tool.

**Goal:** Minimize tokens by providing the agent with enough context to start working.

---

## 2. Tiers (Detail Levels)

### minimal

Minimal context for verifying project availability.

**Content:**
- Project name, slug, status
- Task count by status

**Token estimate:** ~200

**When to use:** Connectivity check, initial overview of available projects.

```
tools/call → get_context_pack
  project_id: "proj_001"
  tier: "minimal"
```

---

### standard

Standard context for starting work on a task.

**Content:**
- Project name, slug, status, description
- Task list (title, status, priority)
- Project git links
- Brief statistics

**Token estimate:** ~1000

**When to use:** Before claim_task. Normal working session.

---

### deep

Deep context for complex tasks.

**Content:**
- Everything from `standard`
- Acceptance Criteria per task
- DoD items per task
- Evidence (last 5 per task)
- Open clarifications
- Project components and modules

**Token estimate:** ~3000

**When to use:** Tasks with complex AC. Reviews. Tasks requiring architectural understanding.

---

### debug

Maximum context for debugging.

**Content:**
- Everything from `deep`
- Audit events (last 20)
- Subtasks per task
- Git commits (last 10)
- Git branches
- Review rounds and findings
- Full metadata of all entities

**Token estimate:** ~5000

**When to use:** Debugging issues. Audit trail analysis. Post-mortem.

---

## 3. ContextSnapshot Model

When working on a task, an agent can capture a context snapshot:

```json
{
  "id": "cs_001",
  "task_id": "task_001",
  "agent_id": "agt_a1b2c3d4",
  "tier": "standard",
  "version": "1.0.0",
  "content_hash": "sha256:a1b2c3...",
  "token_estimate": 1042,
  "content": "# Project: UPCP v2\n\n...",
  "created_at": "2026-07-27T12:00:00Z"
}
```

### Fields

| Field            | Type     | Description                          |
|------------------|----------|--------------------------------------|
| `id`             | UUID     | Unique snapshot ID                   |
| `task_id`        | UUID     | Associated task                      |
| `agent_id`       | UUID     | Agent that created the snapshot      |
| `tier`           | enum     | Detail level                         |
| `version`        | semver   | Context pack format version          |
| `content_hash`   | SHA-256  | Content hash for deduplication       |
| `token_estimate` | int      | Token estimate                       |
| `content`        | text     | Markdown content                     |
| `created_at`     | timestamp| Creation time                        |

---

## 4. Versioning

The context pack format is versioned:

| Version | Changes                                  |
|---------|------------------------------------------|
| `1.0.0` | Base format: project, tasks, git links   |

When the format changes, the minor/major version is incremented. Agents can check the version via `content_hash` and cache accordingly.

---

## 5. Token Estimation

`token_estimate` — approximate token count (1 token ≈ 4 characters for English, ≈ 2 characters for code). Used for:

- Selecting a tier before sending to LLM
- Cost monitoring
- Context window overflow warnings

---

## 6. MCP Resource

Context packs are available as an MCP resource:

```
resources/list → [
  { "uri": "context_pack://project/{project_id}", "name": "Project Context Pack" }
]

resources/read → context_pack://project/{project_id}?tier=standard
```

---

## 7. CLI

```bash
# Standard context
upcp context-pack proj_001

# With specific tier
upcp context-pack proj_001 --tier deep

# Save to file
upcp context-pack proj_001 --tier standard --output context.md

# JSON format
upcp context-pack proj_001 --format json
```

---

## 8. Caching

Context packs are cached for 5 minutes. A repeated request with the same `project_id` and `tier` returns the cached version. Cache is invalidated on:

- Task change (status, AC, DoD)
- Evidence attachment
- Git link change
- Project change

---

## 9. Best Practices

1. **Request the minimally sufficient tier.** Do not use `debug` unless necessary.
2. **Cache content_hash.** If the hash hasn't changed, the context is current.
3. **Request the context pack before claim_task**, not after.
4. **For reviews**, use `deep` — AC, DoD, and evidence are needed.
5. **For heartbeat messages**, do not include context — it's overhead.
6. **Save a snapshot** at the start of work — useful for post-mortem.
