# MCP Contract Tests — Specification

> Project: UPCP | Protocol: MCP (Model Context Protocol) | Framework: pytest

## 1. Overview

MCP contract tests ensure that every MCP tool works correctly: accepts valid input, returns expected output, handles errors, and respects permissions.

## 2. MCP Tools

| Tool | Endpoint | Description |
|------|----------|-------------|
| `claim_task` | `POST /tasks/{id}/claim` | Claim a task |
| `heartbeat` | `POST /tasks/{id}/heartbeat` | Heartbeat |
| `report_progress` | `PATCH /tasks/{id}` | Update progress |
| `report_completion` | `POST /tasks/{id}/submit-review` | Complete task |
| `report_blockage` | `POST /tasks/{id}/clarification-request` | Request clarification |
| `read_playbook` | `GET /projects/{id}/playbook` | Read instructions |
| `get_inbox` | `GET /agents/{id}/inbox` | Get inbox |
| `get_task_state` | `GET /tasks/{id}` | Get task state |
| `log_event` | `POST /audit/events` | Log audit event |

## 3. Test structure

```
tests/mcp/
├── conftest.py              # Fixtures: mcp_client, agent_key, tasks
├── test_claim_task.py
├── test_heartbeat.py
├── test_report_progress.py
├── test_report_completion.py
├── test_report_blockage.py
├── test_read_playbook.py
├── test_get_inbox.py
├── test_get_task_state.py
├── test_log_event.py
└── test_contract_errors.py  # Common error cases
```

## 4. What is tested for each tool

For each MCP tool, 5 aspects are verified:

### 4.1 Input Schema Validation

```python
# tests/mcp/test_claim_task.py
class TestClaimTaskInput:
    async def test_valid_input(self, mcp_client, open_task, agent_key):
        result = await mcp_client.call("claim_task", {"task_id": open_task.id}, agent_key)
        assert result["status"] == "claimed"

    async def test_missing_task_id(self, mcp_client, agent_key):
        with pytest.raises(MCPInputError, match="task_id"):
            await mcp_client.call("claim_task", {}, agent_key)

    async def test_invalid_task_id_format(self, mcp_client, agent_key):
        with pytest.raises(MCPInputError):
            await mcp_client.call("claim_task", {"task_id": "not-a-uuid"}, agent_key)

    async def test_extra_fields_rejected(self, mcp_client, agent_key):
        with pytest.raises(MCPInputError):
            await mcp_client.call("claim_task", {"task_id": "xxx", "extra": "field"}, agent_key)
```

### 4.2 Output Schema Validation

```python
class TestClaimTaskOutput:
    async def test_output_schema(self, mcp_client, open_task, agent_key):
        result = await mcp_client.call("claim_task", {"task_id": open_task.id}, agent_key)

        # Verify required fields
        assert "task_id" in result
        assert "status" in result
        assert "claimed_at" in result
        assert result["status"] == "claimed"

        # Verify types
        assert isinstance(result["task_id"], str)
        assert isinstance(result["claimed_at"], str)  # ISO 8601

    async def test_output_matches_spec(self, mcp_client, open_task, agent_key):
        result = await mcp_client.call("claim_task", {"task_id": open_task.id}, agent_key)
        # Validate against JSON Schema from MCP spec
        validate(instance=result, schema=CLAIM_TASK_OUTPUT_SCHEMA)
```

### 4.3 Error Handling

```python
class TestClaimTaskErrors:
    async def test_task_not_found(self, mcp_client, agent_key):
        with pytest.raises(MCPError) as exc:
            await mcp_client.call("claim_task", {"task_id": "nonexistent"}, agent_key)
        assert exc.value.code == "task_not_found"

    async def test_task_already_claimed(self, mcp_client, claimed_task, agent_key):
        with pytest.raises(MCPError) as exc:
            await mcp_client.call("claim_task", {"task_id": claimed_task.id}, agent_key)
        assert exc.value.code == "task_already_claimed"

    async def test_task_not_open(self, mcp_client, done_task, agent_key):
        with pytest.raises(MCPError) as exc:
            await mcp_client.call("claim_task", {"task_id": done_task.id}, agent_key)
        assert exc.value.code == "task_invalid_status"

    async def test_agent_max_claims(self, mcp_client, agent_key_at_limit, open_task):
        with pytest.raises(MCPError) as exc:
            await mcp_client.call("claim_task", {"task_id": open_task.id}, agent_key_at_limit)
        assert exc.value.code == "max_claims_exceeded"
```

### 4.4 Permissions

```python
class TestClaimTaskPermissions:
    async def test_agent_can_claim(self, mcp_client, open_task, agent_key):
        result = await mcp_client.call("claim_task", {"task_id": open_task.id}, agent_key)
        assert result["status"] == "claimed"

    async def test_user_key_cannot_claim(self, mcp_client, open_task, user_key):
        with pytest.raises(MCPError) as exc:
            await mcp_client.call("claim_task", {"task_id": open_task.id}, user_key)
        assert exc.value.code == "permission_denied"

    async def test_agent_cannot_claim_other_project_task(self, mcp_client, other_task, agent_key):
        with pytest.raises(MCPError) as exc:
            await mcp_client.call("claim_task", {"task_id": other_task.id}, agent_key)
        assert exc.value.code == "permission_denied"
```

### 4.5 Idempotency

```python
class TestClaimTaskIdempotency:
    async def test_double_claim_returns_same_result(self, mcp_client, open_task, agent_key):
        r1 = await mcp_client.call("claim_task", {"task_id": open_task.id}, agent_key)
        r2 = await mcp_client.call("claim_task", {"task_id": open_task.id}, agent_key)
        assert r1["task_id"] == r2["task_id"]
        # Second call returns "already claimed" error, does not create a duplicate
```

## 5. Tool-Specific Tests

### 5.1 heartbeat

```python
class TestHeartbeat:
    async def test_heartbeat_valid(self, mcp_client, claimed_task, agent_key):
        result = await mcp_client.call("heartbeat", {
            "task_id": claimed_task.id,
            "message": "Running tests",
            "progress": 75
        }, agent_key)
        assert result["acknowledged"] is True

    async def test_heartbeat_resets_stale_timer(self, mcp_client, stale_task, agent_key):
        await mcp_client.call("heartbeat", {"task_id": stale_task.id}, agent_key)
        task = await get_task(stale_task.id)
        assert task.heartbeat_status == "healthy"

    async def test_heartbeat_on_unclaimed_task(self, mcp_client, open_task, agent_key):
        with pytest.raises(MCPError) as exc:
            await mcp_client.call("heartbeat", {"task_id": open_task.id}, agent_key)
        assert exc.value.code == "task_not_claimed"
```

### 5.2 report_completion

```python
class TestReportCompletion:
    async def test_submit_with_evidence(self, mcp_client, in_progress_task, agent_key, evidence_file):
        result = await mcp_client.call("report_completion", {
            "task_id": in_progress_task.id,
            "summary": "All tests passing, coverage 92%",
            "files_changed": ["src/auth.py", "tests/test_auth.py"],
            "test_results": "42 passed, 0 failed"
        }, agent_key)
        assert result["status"] == "in_review"

    async def test_submit_without_required_evidence(self, mcp_client, in_progress_task, agent_key):
        with pytest.raises(MCPError) as exc:
            await mcp_client.call("report_completion", {
                "task_id": in_progress_task.id,
                "summary": "Done"
            }, agent_key)
        assert exc.value.code == "evidence_incomplete"
```

### 5.3 read_playbook

```python
class TestReadPlaybook:
    async def test_read_existing_playbook(self, mcp_client, project_with_playbook, agent_key):
        result = await mcp_client.call("read_playbook", {
            "project_id": project_with_playbook.id
        }, agent_key)
        assert "agent_instructions" in result
        assert "quality_gates" in result

    async def test_read_project_without_playbook(self, mcp_client, project_no_playbook, agent_key):
        result = await mcp_client.call("read_playbook", {
            "project_id": project_no_playbook.id
        }, agent_key)
        assert result == {"agent_instructions": "", "quality_gates": [], "evidence_requirements": []}
```

## 6. Error Code Reference

| Code | HTTP | Description |
|------|------|-------------|
| `task_not_found` | 404 | Task not found |
| `task_already_claimed` | 409 | Task already claimed |
| `task_invalid_status` | 409 | Invalid status for operation |
| `task_not_claimed` | 409 | Task not claimed by this agent |
| `max_claims_exceeded` | 429 | Claims limit exceeded |
| `permission_denied` | 403 | No permission for operation |
| `evidence_incomplete` | 422 | Required evidence missing |
| `invalid_input` | 422 | Invalid input |
| `rate_limited` | 429 | Rate limit |

## 7. MCP Schema Definitions

```python
# tests/mcp/schemas.py
CLAIM_TASK_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string", "format": "uuid"}
    },
    "required": ["task_id"],
    "additionalProperties": False
}

CLAIM_TASK_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "status": {"type": "string", "const": "claimed"},
        "claimed_at": {"type": "string", "format": "date-time"},
        "heartbeat_interval": {"type": "integer", "minimum": 30, "maximum": 60}
    },
    "required": ["task_id", "status", "claimed_at", "heartbeat_interval"]
}
```

## 8. Running tests

```bash
# All MCP tests
make test-mcp

# Single tool only
pytest tests/mcp/test_claim_task.py -v

# Error cases only
pytest tests/mcp/ -k "error" -v

# With verbose output
pytest tests/mcp/ -v --tb=long
```

## 9. Contract Test Report

```
MCP Contract Test Report
========================
Tool              Input  Output  Error  Perms  Idemp  Total
────────────────────────────────────────────────────────────
claim_task        4/4    2/2     4/4    3/3    1/1    14/14
heartbeat         3/3    2/2     3/3    2/2    1/1    11/11
report_progress   3/3    2/2     2/2    2/2    1/1    10/10
report_completion 4/4    2/2     3/3    2/2    1/1    12/12
report_blockage   3/3    2/2     2/2    2/2    1/1    10/10
read_playbook     2/2    2/2     1/1    2/2    1/1     8/8
get_inbox         2/2    2/2     1/1    2/2    1/1     8/8
get_task_state    2/2    2/2     2/2    2/2    1/1     9/9
log_event         3/3    1/1     1/1    1/1    1/1     7/7
────────────────────────────────────────────────────────────
TOTAL: 89/89 passed
```
