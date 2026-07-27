# Runbook: Stale Claims

> Project: UPCP | Mechanism: Heartbeat-based stale detection

## 1. Overview

Stale claims — tasks claimed by agents that stopped sending heartbeats. The system automatically detects and releases such tasks.

## 2. Detection Mechanism

### 2.1 Timeouts

| Parameter | Value | Description |
|----------|----------|----------|
| `HEARTBEAT_INTERVAL` | 30-60 sec | Recommended heartbeat interval |
| `HEARTBEAT_STALE` | 7 min | Task is considered stale |
| `HEARTBEAT_DEAD` | 15 min | Automatic release |
| `HEARTBEAT_CHECK_INTERVAL` | 1 min | How often the system checks |

### 2.2 State machine

```
claimed ──(7 min without heartbeat)──→ stale ──(another 8 min)──→ auto_released → open
  │                                    │
  │                                    └→ heartbeat_received → claimed (timer reset)
  │
  └──(heartbeat ok)──→ claimed (extension)
```

### 2.3 Implementation

```python
# Periodic task (celery/apscheduler or cron endpoint)
async def check_stale_claims():
    stale_threshold = datetime.utcnow() - timedelta(minutes=7)
    dead_threshold = datetime.utcnow() - timedelta(minutes=15)

    stale_tasks = await db.execute(
        select(Task)
        .where(Task.status == "claimed")
        .where(Task.last_heartbeat_at < stale_threshold)
    )

    for task in stale_tasks:
        if task.last_heartbeat_at < dead_threshold:
            # Auto-release
            await release_task(task, reason="heartbeat_dead")
            await notify(task.project.owner, "task.auto_released", task)
        else:
            # Mark stale
            await mark_stale(task)
            await notify(task.project.owner, "task.stale", task)
```

## 3. How to Identify Stale Claims

### 3.1 Via API

```bash
# List stale tasks of a project
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:38080/api/v1/projects/PROJECT_ID/tasks?status=claimed&stale=true"

# Details of a specific task
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:38080/api/v1/tasks/TASK_ID"
# Check the last_heartbeat_at and heartbeat_status fields
```

### 3.2 Via Database

```bash
# Find stale claims
docker compose exec db psql -U upcp -c "
  SELECT
    t.id,
    t.title,
    t.agent_id,
    t.last_heartbeat_at,
    NOW() - t.last_heartbeat_at AS time_since_heartbeat
  FROM tasks t
  WHERE t.status = 'claimed'
    AND t.last_heartbeat_at < NOW() - INTERVAL '7 minutes'
  ORDER BY t.last_heartbeat_at ASC;"

# Find dead claims (auto-release candidates)
docker compose exec db psql -U upcp -c "
  SELECT id, title, agent_id, last_heartbeat_at
  FROM tasks
  WHERE status = 'claimed'
    AND last_heartbeat_at < NOW() - INTERVAL '15 minutes';"
```

### 3.3 Via Grafana

Dashboard: **Agent Activity** → Panels:
- **Heartbeat Status**: healthy / stale / dead
- **Stale Detections**: count per period
- **Claims by Agent**: table with last heartbeat

### 3.4 Via Logs

```bash
# Search for stale events
docker compose logs app --tail 1000 | grep "stale"

# Example log:
# 2026-07-27 14:30:00 WARNING task.stale_detected task_id=142 agent=claude-agent-3 heartbeat_age=8m30s
```

## 4. How to Release a Stale Claim

### 4.1 Automatically (system)

The system automatically releases dead claims (>15 min). No manual intervention required.

### 4.2 Manually (administrator)

```bash
# Via API
curl -X POST -H "Authorization: Bearer TOKEN" \
  "http://localhost:38080/api/v1/tasks/TASK_ID/release" \
  -d '{"reason": "manual_release_stale"}'

# Via database (emergency)
docker compose exec db psql -U upcp -c "
  UPDATE tasks
  SET status = 'open', agent_id = NULL, claimed_at = NULL, last_heartbeat_at = NULL
  WHERE id = 'TASK_ID' AND status IN ('claimed', 'stale');"
```

### 4.3 Via UI

Attention Dashboard → Stale section → [Release] button on the task card.

## 5. How to Reassign a Task

### 5.1 Same agent (retry)

```bash
# Agent can re-claim after release
curl -X POST -H "Authorization: ApiKey AGENT_KEY" \
  "http://localhost:38080/api/v1/tasks/TASK_ID/claim"
```

### 5.2 Different agent

```bash
# Assign a specific agent (admin)
curl -X POST -H "Authorization: Bearer TOKEN" \
  "http://localhost:38080/api/v1/tasks/TASK_ID/assign" \
  -d '{"agent_id": "OTHER_AGENT_ID"}'
```

### 5.3 Round-robin (automatic)

If auto-assign is configured, the task is automatically assigned to the next available agent after release.

## 6. Monitoring

### 6.1 Alerts

```yaml
groups:
  - name: stale-claims
    rules:
      - alert: StaleClaimsDetected
        expr: upcp_tasks_stale_total > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $value }} stale claims detected"

      - alert: FrequentAutoReleases
        expr: rate(upcp_tasks_auto_released_total[10m]) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Frequent auto-releases: possible agent health issue"

      - alert: NoHeartbeats
        expr: rate(upcp_heartbeat_total[3m]) == 0
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "No heartbeats received for 3 minutes"
```

### 6.2 Metrics

| Metric | Type | Description |
|---------|-----|----------|
| `upcp_tasks_stale_total` | counter | Total stale detections |
| `upcp_tasks_auto_released_total` | counter | Automatic releases |
| `upcp_heartbeat_age_seconds` | gauge | Age of last heartbeat |
| `upcp_claims_active` | gauge | Active claims |

## 7. Prevention

### 7.1 Agent-side

```python
# Example heartbeat loop for an agent
import asyncio
import httpx

async def work_on_task(task_id: str, api_key: str):
    async with httpx.AsyncClient() as client:
        while True:
            # Do work...
            await do_work_step()

            # Send heartbeat
            await client.post(
                f"{API_URL}/tasks/{task_id}/heartbeat",
                headers={"Authorization": f"ApiKey {api_key}"},
                json={"message": "Working...", "progress": current_progress}
            )

            await asyncio.sleep(30)  # every 30 seconds
```

### 7.2 UPCP-side

- Playbook specifies `heartbeat_interval: 30` as a recommendation
- On claim, the agent receives a heartbeat reminder
- Inbox message on first stale warning (before auto-release)

### 7.3 Agent health checks

```bash
# Check which agents are active
docker compose exec db psql -U upcp -c "
  SELECT
    agent_id,
    COUNT(*) as active_claims,
    MAX(last_heartbeat_at) as last_hb
  FROM tasks
  WHERE status IN ('claimed', 'in_progress')
  GROUP BY agent_id
  ORDER BY last_hb ASC;"
```

## 8. Diagnosing Frequent Stale Claims

If stale claims occur regularly:

1. **Check the agent**: is the process running? has it crashed?
2. **Check the network**: can the agent reach the UPCP API?
3. **Check rate limits**: is the rate limiter blocking heartbeats?
4. **Check DNS**: is the server name resolving?
5. **Check load**: is the agent overloaded by a too-large task?
