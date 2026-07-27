# API Design — UPCP v2

## Overview

UPCP provides a REST API for Web UI and external integrations, as well as MCP tools for AI agents. This document describes REST API conventions.

---

## Base URL and Versioning

```
https://{host}/api/v1/{resource}
```

- Version in URL: `/api/v1`
- On breaking changes — new version `/api/v2`, old version supported for at least 6 months
- MCP tools are not versioned (version = server version)

---

## HTTP Methods

| Method | Purpose | Idempotent | Response Body |
|--------|---------|------------|---------------|
| `GET` | Read resource/collection | Yes | Resource or array |
| `POST` | Create resource | No* | Created resource |
| `PUT` | Full replacement | Yes | Updated resource |
| `PATCH` | Partial update | Yes | Updated resource |
| `DELETE` | Delete (soft) | Yes | `204 No Content` |

*POST is idempotent when an `Idempotency-Key` header is present.

---

## Resource Naming

```
/api/v1/projects                           # collection
/api/v1/projects/{project_id}              # specific resource
/api/v1/projects/{project_id}/tasks        # nested collection
/api/v1/projects/{project_id}/tasks/{task_id}
```

**Rules:**
- Names in kebab-case: `review-rounds`, `acceptance-criteria`
- Plural for collections
- UUID v7 as identifiers
- Nesting max 2 levels deep

---

## Authentication

### Web API (JWT)

```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

- Access token: 15 minutes
- Refresh token: 7 days (stored in httpOnly cookie)
- Refresh token rotation on every use

### Agent API (MCP Token)

```http
Authorization: Bearer mcp_{token_prefix}_{random}
```

- Token bound to Agent + scope
- Automatic expiry (configurable)

### API Key (CLI/CI)

```http
X-API-Key: upcp_{key_prefix}_{random}
```

- For CLI and automation
- Bound to user + organization

---

## Pagination

### Request

```http
GET /api/v1/projects?offset=0&limit=20
```

| Parameter | Type | Default | Max |
|-----------|------|---------|-----|
| `offset` | int | 0 | — |
| `limit` | int | 20 | 100 |

### Response

```json
{
  "data": [...],
  "meta": {
    "total": 142,
    "offset": 0,
    "limit": 20,
    "has_more": true
  }
}
```

---

## Filtering

### Syntax

```http
GET /api/v1/tasks?filter[state]=in_progress&filter[priority]=high
```

### Operators

```http
filter[field]=value           # exact match
filter[field_gt]=value        # greater than
filter[field_gte]=value       # greater than or equal
filter[field_lt]=value        # less than
filter[field_lte]=value       # less than or equal
filter[field_like]=value      # LIKE (substring)
filter[field_in]=a,b,c        # IN (list)
filter[field_null]=true       # IS NULL
```

### Rules

- Filtering only by whitelisted fields (restricted per-endpoint)
- No arbitrary SQL expressions
- Max 5 filters per request

---

## Sorting

```http
GET /api/v1/tasks?sort=-created_at,title
```

- Prefix `-` = DESC, no prefix = ASC
- Multiple fields separated by comma
- Whitelist of allowed fields per-endpoint

**Default:** `-created_at` (newest first)

---

## Error Format

### Structure

```json
{
  "error": {
    "error_code": "VALIDATION_ERROR",
    "message": "The 'title' field is required",
    "hint": "Provide a task title",
    "entity": "task",
    "entity_id": null,
    "details": [
      {
        "field": "title",
        "code": "required",
        "message": "This field is required"
      }
    ]
  }
}
```

### Standard Error Codes

| HTTP | error_code | Description |
|------|-----------|-------------|
| 400 | `VALIDATION_ERROR` | Input data validation error |
| 400 | `MALFORMED_REQUEST` | Invalid JSON / format |
| 401 | `AUTHENTICATION_REQUIRED` | No token |
| 401 | `TOKEN_EXPIRED` | Token expired |
| 403 | `PERMISSION_DENIED` | No permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | State conflict (duplicate, state machine) |
| 409 | `ALREADY_EXISTS` | Resource already exists |
| 422 | `UNPROCESSABLE_ENTITY` | Business validation failed |
| 429 | `RATE_LIMITED` | Rate limit exceeded |
| 500 | `INTERNAL_ERROR` | Internal error |
| 503 | `SERVICE_UNAVAILABLE` | Dependency unavailable |

### Rules

- `message` — human-readable description (may be in user's language)
- `error_code` — machine-readable, stable
- `details` — array of field errors (for validation)
- `entity` + `entity_id` — error context
- Never expose internal details (stack trace, SQL)

---

## Rate Limiting

### Response Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1699999999
Retry-After: 30
```

### On Exceeding (429)

```json
{
  "error": {
    "error_code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "hint": "Retry after 30 seconds",
    "details": {
      "limit": 100,
      "window_seconds": 60,
      "retry_after_seconds": 30
    }
  }
}
```

---

## Idempotency

### Header

```http
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

### Rules

- Required for `POST` requests (creation)
- Optional for `PUT`/`PATCH`/`DELETE`
- UUID v4, generated by the client
- Key lives 24 hours in Redis
- On repeat request with the same key — cached response is returned
- On conflict (different body) — `409 CONFLICT`

---

## Typical Responses

### Successful Creation (201)

```http
HTTP/1.1 201 Created
Location: /api/v1/projects/01934b2a-...
Content-Type: application/json

{
  "data": {
    "id": "01934b2a-...",
    "name": "My Project",
    ...
  }
}
```

### Successful Read (200)

```json
{
  "data": { ... }
}
```

### Successful List (200)

```json
{
  "data": [ ... ],
  "meta": { "total": 42, "offset": 0, "limit": 20, "has_more": true }
}
```

### Successful Deletion (204)

```http
HTTP/1.1 204 No Content
```

---

## CORS

```
Access-Control-Allow-Origin: {configured_origin}
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, Idempotency-Key, X-API-Key
Access-Control-Max-Age: 86400
```

---

## Content-Type

- Requests: `application/json`
- Responses: `application/json; charset=utf-8`
- Uploads: `multipart/form-data`
- Exports: `application/octet-stream` (PDF, CSV)

---

## OpenAPI

- Specification is auto-generated from FastAPI
- Available at `/api/v1/openapi.json`
- Swagger UI: `/api/v1/docs` (dev/staging only)
- ReDoc: `/api/v1/redoc` (dev/staging only)
