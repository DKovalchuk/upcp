# MCP Tools Reference

Справочник по MCP tools для агентов. Протокол: JSON-RPC 2.0 over HTTP POST на `/mcp/`.

---

## Read Tools

### whoami

Профиль текущего агента, scopes и assignments.

```json
{ "name": "whoami", "arguments": {} }
// → { "agent_id": "agt_...", "name": "...", "scopes": [...], "assignments": [...] }
```

---

### get_capabilities

Список доступных tools для текущего агента с учётом scope.

```json
{ "name": "get_capabilities", "arguments": {} }
// → { "tools": ["project_list", "claim_task", ...], "scopes": [...] }
```

---

### project_list

Список проектов с пагинацией.

```json
{ "name": "project_list", "arguments": { "offset": 0, "limit": 20 } }
// → { "items": [{ "id", "name", "slug", "status", ... }], "total", "offset", "limit" }
```

---

### project_get

Детали проекта по ID.

```json
{ "name": "project_get", "arguments": { "project_id": "proj_001" } }
// → { "id", "name", "slug", "description", "status", "created_at", "updated_at" }
```

---

### feature_list / feature_get

```json
{ "name": "feature_list", "arguments": { "project_id": "proj_001", "offset": 0, "limit": 50 } }
{ "name": "feature_get", "arguments": { "feature_id": "feat_001" } }
```

---

### task_list

Задачи проекта (через features).

```json
{ "name": "task_list", "arguments": { "project_id": "proj_001", "offset": 0, "limit": 50 } }
// → { "items": [{ "id", "feature_id", "title", "status", "priority", "assignee_type", ... }], "total" }
```

---

### task_get

Задача + вложенные `acceptance_criteria[]`, `dod_items[]`, `subtasks[]`.

```json
{ "name": "task_get", "arguments": { "task_id": "task_001" } }
```

---

### get_context_pack

Markdown-контекст проекта. Tiers: `minimal` | `standard` | `deep` | `debug`. См. [context-packs.md](./context-packs.md).

```json
{ "name": "get_context_pack", "arguments": { "project_id": "proj_001", "tier": "standard" } }
```

---

### get_agent_inbox

Входящие clarification requests. Filter: `open` | `answered` | `blocking`.

```json
{ "name": "get_agent_inbox", "arguments": { "status": "open" } }
// → { "items": [{ "id", "task_id", "question", "status", "created_at" }] }
```

---

### list_evidence

Evidence, прикреплённые к задаче.

```json
{ "name": "list_evidence", "arguments": { "task_id": "task_001" } }
// → { "items": [{ "id", "evidence_type", "content", "url", "verified", "created_at" }] }
```

---

### list_review_rounds

Раунды ревью задачи.

```json
{ "name": "list_review_rounds", "arguments": { "task_id": "task_001" } }
// → { "items": [{ "id", "round_number", "status", "verdict", "findings_count" }] }
```

---

## Write Tools

### claim_task

Атомарный захват задачи. Требуется `idempotency_key` (UUID v4).

```json
{ "name": "claim_task", "arguments": { "task_id": "task_001", "idempotency_key": "<uuid>" } }
// → { "task_id", "claim_id", "agent_id", "claimed_at", "expires_at" }
// Ошибки: TASK_ALREADY_CLAIMED, TASK_NOT_CLAIMABLE, IDEMPOTENCY_CONFLICT
```

---

### release_task

Освобождает задачу.

```json
{ "name": "release_task", "arguments": { "task_id": "task_001", "reason": "requires clarification" } }
```

---

### heartbeat_task

Сигнал жизни. Обновляет TTL claim. Каждые 30–60 сек. Без heartbeat — claim истекает через 30 мин.

```json
{ "name": "heartbeat_task", "arguments": { "task_id": "task_001", "message": "analyzing codebase" } }
```

---

### report_progress

Фиксация прогресса.

```json
{ "name": "report_progress", "arguments": { "task_id": "task_001", "summary": "tests written", "progress_percent": 40 } }
```

---

### attach_evidence

Прикрепление доказательства. Типы: `test_output`, `screenshot`, `log`, `url`, `file`.

```json
{ "name": "attach_evidence", "arguments": {
  "task_id": "task_001", "evidence_type": "test_output",
  "content": "pytest: 47 passed in 3.2s"
} }
```

---

### request_clarification

Запрос уточнения. `blocking: true` — задача в `blocked`. `false` — продолжается.

```json
{ "name": "request_clarification", "arguments": {
  "task_id": "task_001",
  "question": "Should due_date use ISO 8601 or Unix timestamp?",
  "blocking": true
} }
```

---

### reply_clarification

Ответ на clarification request.

```json
{ "name": "reply_clarification", "arguments": {
  "clarification_id": "clr_001", "answer": "Use ISO 8601 format"
} }
```

---

### submit_task_for_review

Отправка на ревью. Требования: все DoD `passed`, нет blocking clarifications, хотя бы один evidence.

```json
{ "name": "submit_task_for_review", "arguments": {
  "task_id": "task_001", "summary": "CRUD implemented, all tests green."
} }
// Ошибки: DOD_NOT_SATISFIED, EVIDENCE_REQUIRED, CLARIFICATION_BLOCKING
```

---

### create_review_finding

Находка в раунде ревью (для reviewer-агентов). Severity: `info|low|medium|high|critical`. Category: `code_quality|security|performance|correctness`.

```json
{ "name": "create_review_finding", "arguments": {
  "review_round_id": "rr_001", "severity": "medium",
  "category": "code_quality",
  "description": "Missing error handling in create()",
  "file_path": "backend/app/users/service.py", "line_range": "42-58"
} }
```

---

### submit_review_verdict

Финальный вердикт. Verdict: `approve` | `reject` | `needs_changes`.

```json
{ "name": "submit_review_verdict", "arguments": {
  "review_round_id": "rr_001", "verdict": "needs_changes",
  "summary": "Add error handling and edge case tests."
} }
```

---

## Идиемпотентность

Write tools принимают `idempotency_key` (UUID v4). Повторный запрос с тем же ключом возвращает предыдущий результат. Ключи хранятся 24 часа.

## Пагинация

List tools: `offset` (default: 0), `limit` (default: 20, max: 100).
