# TASK-0076 MCP Workflow Tools

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M9

## Goal

Add workflow MCP tools: claim, release, heartbeat, clarification.

## Dependencies

- TASK-0074 (agent workflow endpoints)
- TASK-0075 (agent inbox)

## Files likely involved

```text
backend/app/mcp/tools.py               # add workflow tools
backend/tests/test_mcp.py              # add workflow tool tests
```

## New MCP Tools

| Tool | Description | Input |
|------|-------------|-------|
| `claim_task` | Claim task for agent | { task_id, context_snapshot? } |
| `release_task` | Release claim | { task_id } |
| `heartbeat_task` | Send heartbeat | { task_id, progress_percent, current_step, next_step, blockers?, eta? } |
| `request_clarification` | Ask question | { task_id, question, context?, blocking } |
| `answer_clarification` | Answer question | { clarification_id, answer } |
| `submit_task_for_review` | Submit for review | { task_id } |
| `get_agent_inbox` | Agent events | { since? } |
| `get_agent_playbook` | Agent operating guide | {} |

## Acceptance Criteria

- [ ] 8 new MCP tools registered in get_tools().
- [ ] Each tool has input schema and handler.
- [ ] claim_task checks task state and agent permission.
- [ ] release_task checks claim ownership.
- [ ] heartbeat_task validates claim is active.
- [ ] clarification tools create/answer ClarificationRequest.
- [ ] submit_task_for_review transitions to ready_for_review.
- [ ] Tests cover all tools, input validation, error cases.

## DoD

- tests added and passing;
- implementation complete;
- commands pass;
- status updated.
