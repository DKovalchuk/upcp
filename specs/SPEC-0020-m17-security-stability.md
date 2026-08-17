# SPEC-0020 — M17: Security & Stability

**Milestone:** M17
**Version:** 0.19.0
**Status:** PLANNED
**Created:** 2026-08-12
**Source:** M16 Comprehensive Audit (AUDIT_M16_COMPREHENSIVE.md)

## 1. Problem

M16 audit identified critical security and stability issues that must be resolved before continuing feature development:

- **Security:** MCP endpoints bypass auth entirely, LLM providers are stubs, CSP allows unsafe-eval, agent endpoints lack ownership checks
- **Bugs:** Query string construction bug in `fetchProjectTasks`, Project Settings route broken, TopBar items are no-ops, Settings version hardcoded
- **Database:** 17+ missing indexes on FK columns, 27 ForeignKey columns missing `ondelete`, N+1 query in agent detail endpoint
- **Architecture:** Notification trigger silently swallows all exceptions, dead `auth/` module, agent inbox stub, deprecated startup hook

## 2. Scope

### In Scope (4 sprints)

| Sprint | TASK | Focus | Points |
|--------|------|-------|--------|
| S19.1 | TASK-0104 | Critical bug fixes | 5 |
| S19.2 | TASK-0105 | Security hardening | 8 |
| S19.3 | TASK-0106 | Database hardening | 5 |
| S19.4 | TASK-0107 | Architecture cleanup | 5 |

### Out of Scope
- New features (M16 completion continues separately)
- UX redesign (deferred to M18)
- Test infrastructure improvements (deferred to M19)

## 3. Sprint Details

### S19.1: Critical Bug Fixes (TASK-0104)

**5 bugs, 5 points**

| # | Bug | File | Fix |
|---|-----|------|-----|
| 1 | `fetchProjectTasks` query string construction | `frontend/src/lib/api/tasks.ts` | Fix `sep` logic: use `?` for first param, `&` for subsequent |
| 2 | Project Settings route shows Overview tab | `frontend/src/components/project/ProjectDetail.tsx` | Add `'settings'` to TAB_ROUTES map |
| 3 | TopBar Profile/Settings are no-ops | `frontend/src/components/layouts/TopBar.tsx` | Wire to navigate(`/settings`) |
| 4 | Settings version hardcoded `0.14.0` | `frontend/src/components/SettingsPage.tsx` | Read from `/health` response or `package.json` via Vite env |
| 5 | Dashboard "New Project" no-op | `frontend/src/components/Dashboard.tsx` | Navigate to `/projects` + open create dialog |

### S19.2: Security Hardening (TASK-0105)

**5 security issues, 8 points**

| # | Issue | File | Fix |
|---|-------|------|-----|
| 1 | MCP endpoints bypass auth | `identity/middleware.py:52` | Remove `/mcp` skip, require agent token or JWT |
| 2 | LLM providers are stubs | `llm/gateway.py` | Remove stubs, raise `NotImplementedError` with clear message, or implement real providers |
| 3 | CSP allows unsafe-eval | `main.py:122` | Remove `'unsafe-eval'`, add nonce-based script-src |
| 4 | Agent endpoints lack ownership | `identity/agent_endpoints.py` | Add ownership check: user must be admin or agent creator |
| 5 | `env="test"` disables all protections | `main.py:95,99` | Add separate `UPCP_DISABLE_RATE_LIMIT` and `UPCP_DISABLE_AUTH` flags |

### S19.3: Database Hardening (TASK-0106)

**Migration + model fixes, 5 points**

| # | Issue | Fix |
|---|-------|-----|
| 1 | 17+ missing indexes | Add indexes on: `task.feature_id`, `feature.project_id`, `component.project_id`, `module.component_id`, `task.status`, `project.status`, `report.project_id`, `task_claim.agent_id`, `audit_event.*`, gitread FKs |
| 2 | 27 ForeignKey missing ondelete | Add `ondelete="CASCADE"` for child tables, `ondelete="SET NULL"` for optional refs |
| 3 | N+1 in agent detail | Use JOIN or IN clause instead of loop in `agent_endpoints.py:157` |

### S19.4: Architecture Cleanup (TASK-0107)

**5 cleanup items, 5 points**

| # | Issue | File | Fix |
|---|-------|------|-----|
| 1 | Silent exception swallowing | 6 files with `except Exception: pass` | Add `logger.warning()` with context |
| 2 | Dead `auth/` module | `backend/app/auth/` | Delete directory |
| 3 | Agent inbox stub | `api/v1/agent_self.py:69` | Query `AgentInboxEvent` instead of returning empty list |
| 4 | Deprecated startup hook | `main.py:108` | Migrate to FastAPI lifespan context manager |
| 5 | Notification default target "system" | `reporting/trigger.py:99` | Look up actual user from entity context, fallback to "system" only if no user found |

## 4. Testing Strategy

### New Tests Required

| Sprint | Tests | Focus |
|--------|-------|-------|
| S19.1 | 5 frontend tests | Query string fix, route fix, navigation fix |
| S19.2 | 8 backend tests | MCP auth rejection, ownership check, CSP header validation |
| S19.3 | 3 backend tests | Index existence, ondelete cascade behavior, N+1 query count |
| S19.4 | 5 backend tests | Notification error logging, inbox events, lifespan startup |

### Regression

- All 705+ backend tests must pass
- All 260+ frontend tests must pass
- mypy, ruff, tsc clean

## 5. Migration Plan

### Migration 0020: Database Hardening

```sql
-- Indexes
CREATE INDEX ix_task_feature_id ON task(feature_id);
CREATE INDEX ix_feature_project_id ON feature(project_id);
CREATE INDEX ix_component_project_id ON component(project_id);
CREATE INDEX ix_module_component_id ON module(component_id);
CREATE INDEX ix_task_status ON task(status);
CREATE INDEX ix_project_status ON project(status);
CREATE INDEX ix_report_project_id ON report(project_id);
CREATE INDEX ix_task_claim_agent_id ON task_claim(agent_id);
CREATE INDEX ix_audit_event_entity_id ON audit_event(entity_id);
CREATE INDEX ix_audit_event_event_type ON audit_event(event_type);
CREATE INDEX ix_audit_event_timestamp ON audit_event(timestamp);
CREATE INDEX ix_git_provider_project_id ON git_provider(project_id);
CREATE INDEX ix_git_branch_provider_id ON git_branch(provider_id);
CREATE INDEX ix_git_commit_provider_id ON git_commit(provider_id);
CREATE INDEX ix_git_pull_request_provider_id ON git_pull_request(provider_id);
CREATE INDEX ix_git_link_entity ON git_link(entity_type, entity_id);

-- ondelete changes (Alembic will generate ALTER TABLE statements)
-- Child tables: CASCADE
-- Optional refs: SET NULL
```

## 6. Definition of Done

- [ ] All 5 critical bugs fixed and verified
- [ ] MCP endpoints require authentication
- [ ] LLM providers removed or properly implemented
- [ ] CSP hardened (no unsafe-eval)
- [ ] All FK columns have indexes
- [ ] All ForeignKeys have ondelete
- [ ] Notification triggers log errors instead of swallowing
- [ ] Dead auth/ module removed
- [ ] Agent inbox returns real events
- [ ] All existing tests pass
- [ ] New tests pass (21 total)
- [ ] mypy, ruff, tsc clean
- [ ] Docs updated
