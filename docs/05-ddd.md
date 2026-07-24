# DDD Rules

UPCP uses bounded contexts inside a modular monolith.

## Contexts

```text
health
shared
projects
structure
delivery
quality
gitread
reporting
llm
audit
mcp
api
```

## Context responsibilities

### health

Liveness/readiness endpoints.

### shared

Cross-cutting utilities:

- config;
- logging;
- errors;
- pagination;
- ids;
- time.

### projects

Project lifecycle and metadata.

### structure

Components and modules.

### delivery

Features, tasks, subtasks.

### quality

Acceptance criteria and DoD.

### gitread

Read-only Git provider integration.

### reporting

Daily/weekly/portfolio reports.

### llm

Optional LLM gateway and redaction.

### audit

Immutable audit events.

### mcp

MCP tools and resources.

### api

HTTP routers and API composition.

## Dependency rules

```text
interfaces -> application/services -> domain
infrastructure -> application interfaces
```

Avoid:

- direct import of internal details from another context;
- cross-context tight coupling;
- shared mutable state;
- god services.
