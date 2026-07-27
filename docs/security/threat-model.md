# Threat Model — UPCP v2 (STRIDE)

> Scope: `security` | Version: 2.0.0

## 1. Overview

The threat model is built using the STRIDE methodology. Each threat: description, attack vector, impact, mitigation.

## 2. System Context

```
Browser/React 19 → FastAPI (Python 3.12) → PostgreSQL
                       ↓
                     Redis
                       ↓
                  AI Agents (MCP)
```

## 3. Spoofing

**S1: Agent impersonation via stolen token**
- Vector: agent token leaked from CI/CD, env, logs → impersonator performs tasks
- Mitigation: SecretProvider, scope restriction (token bound to project), 30-day rotation, audit event on every use

**S2: User impersonation via stolen session**
- Vector: XSS → access token theft, or stolen refresh token
- Mitigation: access token in memory only (not localStorage), refresh token httpOnly/Secure/SameSite=Strict, CSP headers, token rotation, reuse detection (reused revoked refresh → entire chain revoked)

**S3: Credential stuffing**
- Vector: mass login attempts with stolen credentials
- Mitigation: rate limit 5 attempts/min/IP, 15 min lockout after 5 failures, breached password check (HaveIBeenPwned, k-anonymity)

## 4. Tampering

**T1: Task/result modification by agents**
- Vector: agent with excessive permissions modifies other agents' tasks
- Mitigation: agent works only with claimed tasks, immutable after submit, audit log hash chain, reviewer approve/reject

**T2: Injection via MCP tools**
- Vector: prompt injection → arbitrary MCP calls
- Mitigation: tool allowlist, argument validation/sanitization, rate limit 200/min/token, audit log with arguments, MCP server isolation (separate containers)

**T3: SQL injection**
- Vector: malicious input via API
- Mitigation: SQLAlchemy 2 ORM (parameterized queries), Pydantic validation, raw SQL forbidden, minimal DB user privileges

## 5. Repudiation

**R1: Inability to prove an action**
- Vector: user denies having performed an action
- Mitigation: full audit log (timestamp, actor, IP, user_agent), append-only with hash chain, 12-month retention + archive, separate service account for writes

**R2: Audit gaps**
- Vector: actions not recorded in the audit log
- Mitigation: audit event coverage tests, monitoring of event count drops, regular comparison of API endpoints with audit coverage

## 6. Information Disclosure

**I1: Secret leakage via API**
- Vector: errors return secrets in responses
- Mitigation: redaction layer on all responses, password/token/secret fields forbidden, tests, error handler without stack trace in production

**I2: Secret leakage via logs**
- Vector: logs contain passwords, tokens, connection strings
- Mitigation: RedactingLogger with pattern matching, password/token/secret/key logging forbidden, code review, automated log scanning

**I3: Cross-project agent access**
- Vector: agent requests data outside project scope
- Mitigation: scope enforcement at middleware level (token.project_id == resource.project_id), audit event on attempt

**I4: SQL errors with schema details**
- Vector: unhandled SQL exceptions in responses
- Mitigation: global exception handler (generic error), details in logs only, tests

## 7. Denial of Service

**D1: API abuse / rate limiting bypass**
- Mitigation: rate limiting by IP/user/agent/token (see `rate-limiting.md`), abuse detection with blocking, connection pooling, request timeout 30 sec (API) / 10 sec (auth)

**D2: Resource exhaustion via agents**
- Mitigation: limit of 10 tasks in progress per agent, files ≤50 MB, ≤1000 files per project, 30 min task timeout

**D3: Database overload**
- Mitigation: mandatory pagination (max 100), 10 sec query timeout, connection pool 5–20, read replicas (future)

## 8. Elevation of Privilege

**E1: RBAC bypass via API**
- Mitigation: permission check on every endpoint (decorator-based), middleware: auth → authz → handler, default deny, tests for every role on every endpoint

**E2: Role manipulation**
- Vector: user assigns themselves a higher role
- Mitigation: role assignment only via `admin.role.assign`, one Owner per organization, self-role-change forbidden, audit event on change

**E3: Agent token escalation**
- Vector: agent attempts to obtain permissions above its role
- Mitigation: fixed role after token creation, scope enforcement, max agent role: Member (never Admin/Owner), audit on attempt

## 9. Risk Matrix

| ID  | Threat                       | Probability | Impact    | Risk    | Mitigation  |
|-----|------------------------------|:-----------:|:---------:|:-------:|:-----------:|
| S1  | Agent impersonation          | Medium      | High      | High    | ✅ Done     |
| S2  | User impersonation           | Low         | Critical  | High    | ✅ Done     |
| S3  | Credential stuffing          | Medium      | Medium    | Medium  | ✅ Done     |
| T1  | Task modification            | Low         | Medium    | Medium  | ✅ Done     |
| T2  | MCP prompt injection         | High        | High      | High    | ⚠️ Partial  |
| T3  | SQL injection                | Low         | Critical  | High    | ✅ Done     |
| R1  | Action repudiation           | Medium      | Low       | Low     | ✅ Done     |
| R2  | Audit gaps                   | Medium      | Medium    | Medium  | ⚠️ Partial  |
| I1  | Secret leakage (API)         | Low         | Critical  | High    | ✅ Done     |
| I2  | Secret leakage (logs)        | Medium      | High      | High    | ✅ Done     |
| I3  | Cross-project access         | Low         | High      | Medium  | ✅ Done     |
| I4  | SQL errors                   | Low         | Low       | Low     | ✅ Done     |
| D1  | API abuse                    | High        | Medium    | Medium  | ✅ Done     |
| D2  | Resource exhaustion          | Medium      | Medium    | Medium  | ✅ Done     |
| D3  | Database overload            | Low         | High      | Medium  | ⚠️ Partial  |
| E1  | RBAC bypass                  | Low         | Critical  | High    | ✅ Done     |
| E2  | Role manipulation            | Low         | Critical  | High    | ✅ Done     |
| E3  | Agent token escalation       | Low         | High      | Medium  | ✅ Done     |
