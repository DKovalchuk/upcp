# System Context — UPCP v2

## Overview

UPCP (Universal Project Control Plane) is a self-contained, local-first platform for collaborative work between humans and AI agents on engineering projects. This document describes system boundaries and interaction with external actors.

---

## Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        External Actors                                  │
│                                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────────┐ │
│   │  Owner   │    │AI Agent  │    │ MCP Client   │    │Git Provider  │ │
│   │ (human)  │    │ (LLM-    │    │ (Cursor,     │    │ (GitLab,     │ │
│   │          │    │  agent)  │    │  Claude,     │    │  GitHub)     │ │
│   │          │    │          │    │  Qwen Code)  │    │              │ │
│   └────┬─────┘    └────┬─────┘    └──────┬───────┘    └──────┬───────┘ │
│        │               │                │                    │         │
└────────┼───────────────┼────────────────┼────────────────────┼─────────┘
         │               │                │                    │
         ▼               ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     UPCP Platform                                │   │
│   │                                                                  │   │
│   │   ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │   │
│   │   │  FastAPI App │   │  MCP Server  │   │       CLI        │   │   │
│   │   │  (REST API)  │   │  (stdio/     │   │  (upcp-cli)      │   │   │
│   │   │              │   │   SSE/HTTP)  │   │                  │   │   │
│   │   └──────┬───────┘   └──────┬───────┘   └────────┬─────────┘   │   │
│   │          │                  │                     │             │   │
│   │          └──────────────────┼─────────────────────┘             │   │
│   │                             │                                   │   │
│   │                   ┌─────────▼──────────┐                        │   │
│   │                   │  Core Domain Layer │                        │   │
│   │                   │  (bounded contexts)│                        │   │
│   │                   └─────────┬──────────┘                        │   │
│   │                             │                                   │   │
│   └─────────────────────────────┼───────────────────────────────────┘   │
│                                 │                                       │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌────────────────┐   ┌───────────────────┐   ┌──────────────────────────┐
│  PostgreSQL    │   │      Redis        │   │  OpenTelemetry Collector │
│  (primary DB)  │   │  (cache, rate     │   │  (traces, metrics, logs) │
│                │   │   limits, queues, │   │                          │
│                │   │   pub/sub)        │   │                          │
└────────────────┘   └───────────────────┘   └────────────┬─────────────┘
                                                          │
                                                          ▼
                                              ┌──────────────────────────┐
                                              │  Grafana Stack           │
                                              │  ├── Grafana (dashboards)│
                                              │  ├── Loki (logs)         │
                                              │  ├── Tempo (traces)      │
                                              │  └── Prometheus (metrics)│
                                              └──────────────────────────┘
```

---

## Actors

| Actor | Role | Interaction Channel |
|-------|------|---------------------|
| **Owner** | Project owner, manages agents, makes decisions | Web UI, CLI |
| **AI Agent** | Executes tasks, provides evidence, requests clarifications | MCP protocol |
| **MCP Client** | Agent host application (Cursor, Claude Desktop, Qwen Code) | MCP over stdio/SSE/HTTP |
| **Git Provider** | External SCM system for commit and branch synchronization | Webhook + REST API |

---

## External Systems

| System | Purpose | Protocol |
|--------|---------|----------|
| **PostgreSQL 16** | Primary relational DB | asyncpg / SQLAlchemy 2 |
| **Redis 7** | Cache, rate limiting, pub/sub, queues | redis-py (async) |
| **OpenTelemetry Collector** | Telemetry collection | OTLP gRPC/HTTP |
| **Grafana** | Dashboard visualization | HTTP |
| **Loki** | Log aggregation | HTTP push |
| **Tempo** | Trace storage | OTLP |
| **Prometheus** | Metrics storage | scrape / remote write |

---

## Internal Components

### FastAPI App
- REST API for Web UI and external integrations
- JWT authentication, RBAC
- OpenTelemetry middleware
- Rate limiting via Redis

### MCP Server
- Model Context Protocol implementation
- Transports: stdio (for local clients), SSE, HTTP
- Tools: read/write/admin analogous to REST API
- Token-based authentication for agents

### CLI (upcp-cli)
- Command-line shell for owners and CI/CD
- Authentication via API keys or JWT
- Commands: project, agent, task, review, report

---

## Trust Boundaries

```
┌─ Trusted Zone (self-hosted) ────────────────────────────┐
│  FastAPI + MCP Server + CLI + PostgreSQL + Redis         │
└──────────────────────────────────────────────────────────┘
         ▲                    ▲                   ▲
    JWT / API Key        MCP Token           Webhook Secret
         │                    │                   │
┌────────┴───┐    ┌──────────┴────┐    ┌─────────┴────────┐
│ Owner/UI   │    │ AI Agent/     │    │ Git Provider     │
│ (browser)  │    │ MCP Client    │    │ (external SCM)   │
└────────────┘    └───────────────┘    └──────────────────┘
```

- All incoming connections are authenticated
- MCP agents receive scoped tokens with project-level restrictions
- Webhooks from Git providers are verified via HMAC signature
- No outgoing connections to LLM providers (agents operate through MCP clients)
