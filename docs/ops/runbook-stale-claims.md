# Runbook: Stale Claims

> Проект: UPCP | Механизм: Heartbeat-based stale detection

## 1. Обзор

Stale claims — задачи, захваченные агентами, которые перестали отправлять heartbeat. Система автоматически обнаруживает и освобождает такие задачи.

## 2. Механизм детекции

### 2.1 Таймауты

| Параметр | Значение | Описание |
|----------|----------|----------|
| `HEARTBEAT_INTERVAL` | 30-60 сек | Рекомендуемый интервал heartbeat |
| `HEARTBEAT_STALE` | 7 мин | Задача считается stale |
| `HEARTBEAT_DEAD` | 15 мин | Автоматический release |
| `HEARTBEAT_CHECK_INTERVAL` | 1 мин | Как часто система проверяет |

### 2.2 State machine

```
claimed ──(7 мин без heartbeat)──→ stale ──(ещё 8 мин)──→ auto_released → open
  │                                    │
  │                                    └→ heartbeat_received → claimed (сброс таймера)
  │
  └──(heartbeat ok)──→ claimed (продление)
```

### 2.3 Реализация

```python
# Периодическая задача (celery/apscheduler или cron endpoint)
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

## 3. Как идентифицировать stale claims

### 3.1 Через API

```bash
# Список stale задач проекта
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:38080/api/v1/projects/PROJECT_ID/tasks?status=claimed&stale=true"

# Детали конкретной задачи
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:38080/api/v1/tasks/TASK_ID"
# Смотреть поле last_heartbeat_at и heartbeat_status
```

### 3.2 Через БД

```bash
# Найти stale claims
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

# Найти dead claims (auto-release кандидаты)
docker compose exec db psql -U upcp -c "
  SELECT id, title, agent_id, last_heartbeat_at
  FROM tasks
  WHERE status = 'claimed'
    AND last_heartbeat_at < NOW() - INTERVAL '15 minutes';"
```

### 3.3 Через Grafana

Dashboard: **Agent Activity** → Panels:
- **Heartbeat Status**: healthy / stale / dead
- **Stale Detections**: количество за период
- **Claims by Agent**: таблица с last heartbeat

### 3.4 Через логи

```bash
# Поиск stale events
docker compose logs app --tail 1000 | grep "stale"

# Пример лога:
# 2026-07-27 14:30:00 WARNING task.stale_detected task_id=142 agent=claude-agent-3 heartbeat_age=8m30s
```

## 4. Как освободить stale claim

### 4.1 Автоматически (система)

Система автоматически release dead claims (>15 мин). Не требует ручного вмешательства.

### 4.2 Вручную (администратор)

```bash
# Через API
curl -X POST -H "Authorization: Bearer TOKEN" \
  "http://localhost:38080/api/v1/tasks/TASK_ID/release" \
  -d '{"reason": "manual_release_stale"}'

# Через БД (экстренно)
docker compose exec db psql -U upcp -c "
  UPDATE tasks
  SET status = 'open', agent_id = NULL, claimed_at = NULL, last_heartbeat_at = NULL
  WHERE id = 'TASK_ID' AND status IN ('claimed', 'stale');"
```

### 4.3 Через UI

Attention Dashboard → Stale секция → [Release] кнопка на карточке задачи.

## 5. Как переназначить задачу

### 5.1 Тот же агент (retry)

```bash
# Агент может claim повторно после release
curl -X POST -H "Authorization: ApiKey AGENT_KEY" \
  "http://localhost:38080/api/v1/tasks/TASK_ID/claim"
```

### 5.2 Другой агент

```bash
# Назначить конкретного агента (admin)
curl -X POST -H "Authorization: Bearer TOKEN" \
  "http://localhost:38080/api/v1/tasks/TASK_ID/assign" \
  -d '{"agent_id": "OTHER_AGENT_ID"}'
```

### 5.3 Round-robin (автоматически)

Если настроен auto-assign, задача автоматически назначается следующему свободному агенту после release.

## 6. Мониторинг

### 6.1 Алёрты

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

### 6.2 Метрики

| Метрика | Тип | Описание |
|---------|-----|----------|
| `upcp_tasks_stale_total` | counter | Всего stale detections |
| `upcp_tasks_auto_released_total` | counter | Автоматических releases |
| `upcp_heartbeat_age_seconds` | gauge | Возраст последнего heartbeat |
| `upcp_claims_active` | gauge | Активные claims |

## 7. Предотвращение

### 7.1 На стороне агента

```python
# Пример heartbeat loop для агента
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

            await asyncio.sleep(30)  # каждые 30 секунд
```

### 7.2 На стороне UPCP

- Playbook указывает `heartbeat_interval: 30` как рекомендацию
- При claim агент получает напоминание о heartbeat
- Inbox сообщение при первом stale warning (до auto-release)

### 7.3 Health checks агентов

```bash
# Проверить, какие агенты активны
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

## 8. Диагностика частых stale

Если stale claims происходят регулярно:

1. **Проверить агента**: работает ли процесс? не crashed?
2. **Проверить сеть**: может ли агент достучаться до UPCP API?
3. **Проверить rate limits**: не блокирует ли rate limiter heartbeat?
4. **Проверить DNS**: резолвится ли имя сервера?
5. **Проверить нагрузку**: не перегружен ли агент слишком большой задачей?
