# CLI Commands for Agents

Reference for UPCP CLI commands for agents. Entry point: `upcp`.

---

## Global Flags

| Flag            | Description                      | Default                        |
|-----------------|----------------------------------|--------------------------------|
| `--token TOKEN` | Agent token (or `UPCP_AGENT_TOKEN` env) | —                      |
| `--url URL`     | API base URL (or `UPCP_API_URL` env)     | `http://localhost:38080` |
| `--format FORMAT` | `json` or `table`              | `table`                        |
| `--verbose`     | Verbose output                   | `false`                        |

---

## Agent Commands

### upcp agent whoami

Current agent profile.

```bash
upcp agent whoami
# Agent: claude-opus-builder (agt_a1b2c3d4)
# Type: llm · Status: active
# Scopes: projects:read, delivery:write, evidence:write
# Projects: UPCP v2 (contributor)
```

### upcp agent inbox

Incoming clarification requests.

```bash
upcp agent inbox                      # open
upcp agent inbox --status answered    # answered
upcp agent inbox --status blocking    # blocking
# ID        Task       Question                        Status    Created
# clr_001   task_001   "What date format?"            open      2h ago
```

### upcp agent list

Project agents.

```bash
upcp agent list --project-id proj_001
upcp agent list --project-id proj_001 --role reviewer
```

### upcp agent guide

Guide displayed in the console.

```bash
upcp agent guide
```

---

## Task Commands

### upcp task list

```bash
upcp task list proj_001
upcp task list proj_001 --status ready
upcp task list proj_001 --priority 0 --limit 10
upcp task list proj_001 --format json
```

**Filters:** `--status`, `--priority`, `--assignee`, `--feature`, `--offset`, `--limit`.

### upcp task get

```bash
upcp task get task_001
# Task: task_001
# Title: Add User model with RBAC
# Status: ready · Priority: P1 · Assignee: unassigned
# AC: 3/3 defined · DoD: 0/4 passed
```

### upcp task claim

```bash
upcp task claim task_001
# Claimed: task_001 · Claim ID: clm_001
# Expires: 2026-07-27T12:30:00Z
# Remember: send heartbeat every 30-60s
```

Errors: `TASK_ALREADY_CLAIMED`, `TASK_NOT_CLAIMABLE`.

### upcp task release

```bash
upcp task release task_001 --reason "requires clarification on API contract"
```

### upcp task heartbeat

```bash
upcp task heartbeat task_001
upcp task heartbeat task_001 --message "running integration tests"
upcp task heartbeat task_001 --auto --interval 45   # auto in background
```

### upcp task submit-review

```bash
upcp task submit-review task_001 --summary "CRUD implemented, all tests green"
```

Requirements: DoD `passed`, no blocking clarifications, at least one evidence.
Errors: `DOD_NOT_SATISFIED`, `EVIDENCE_REQUIRED`, `CLARIFICATION_BLOCKING`.

---

## Context Pack Commands

### upcp context-pack

```bash
upcp context-pack proj_001                       # standard
upcp context-pack proj_001 --tier minimal         # minimal
upcp context-pack proj_001 --tier deep            # deep
upcp context-pack proj_001 --tier debug           # full
upcp context-pack proj_001 --output context.md    # save to file
```

| Tier        | Content                   | Tokens   |
|-------------|---------------------------|----------|
| `minimal`   | Name, status, task count  | ~200     |
| `standard`  | + tasks, git links        | ~1000    |
| `deep`      | + AC, DoD, evidence       | ~3000    |
| `debug`     | + audit, metadata         | ~5000    |

---

## Evidence Commands

```bash
upcp evidence list task_001
upcp evidence attach task_001 --type test_output --content "pytest: 47 passed"
upcp evidence attach task_001 --type url --url "https://github.com/.../pull/42"
```

---

## Clarification Commands

```bash
upcp clarification request task_001 --question "UUID or auto-increment?" --blocking
upcp clarification reply clr_001 --answer "Use UUID v4 as per project convention"
```

---

## Status Command

```bash
upcp status
# API:        ✅ http://localhost:38080 (200 OK)
# Database:   ✅ connected
# Redis:      ✅ connected
# MCP:        ✅ 12 tools registered
# Agent:      ✅ claude-opus-builder (agt_a1b2c3d4)
```

---

## Environment Variables

| Variable            | Description             | Default                      |
|---------------------|-------------------------|------------------------------|
| `UPCP_API_URL`      | Base URL                | `http://localhost:38080`     |
| `UPCP_AGENT_TOKEN`  | Agent token             | —                            |
| `UPCP_FORMAT`       | Output format           | `table`                      |
| `UPCP_TIMEOUT`      | HTTP timeout (seconds)  | `30`                         |
