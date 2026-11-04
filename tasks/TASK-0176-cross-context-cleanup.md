# TASK-0176 — Cross-context cleanup: agent_endpoints / agent_self без прямых запросов к чужим моделям

**Source:** SPEC-0029 §3.6 (S29.6), audit finding 9; AGENTS.md §5 (DDD)
**Milestone:** auth rework (SPEC-0029 batch)
**Spec:** SPEC-0029 §3.6, AC7
**Points:** 5
**Status:** DONE (2026-11-04 — реализация + evidence ниже)

## Context

`identity/agent_endpoints.py` импортирует и запрашивает
`app.delivery.models` (Task, TaskClaim, Heartbeat, AgentInboxEvent,
ClarificationRequest) и `app.quality.models` (Evidence, ReviewRound) —
~20 прямых cross-context запросов; `api/v1/agent_self.py` — прямые
запросы к delivery (TaskClaim, ClarificationRequest, AgentInboxEvent).
Это нарушение AGENTS §5 («Do not import internal implementation details
from another context»), дважды «проглоченное» аудитами (SPEC-0029
finding 9).

## Goals

1. Вынести чтение delivery/quality-данных за пределы identity-роутов в
   **public-сервисы** контекстов-владельцев (delivery: claim/inbox/
   clarification-чтение; quality: evidence/review-round чтение) —
   identity-роуты потребляют только публичный контракт сервиса
   (схема/DTO), не модели.
2. Идентично для `api/v1/agent_self.py` (это api-слой, но правило то же:
   запросы — через сервисы-владельцы).
3. Кросс-контекстные JOIN'ы, если есть (проверить SQL) — разбить на
   сервис-уровне (AGENTS §5: avoid cross-context direct DB joins).
4. Перенос без смены поведения: коды ответов, пагинация, фильтры —
   characterization-тесты существующие, семантика не меняется.

## Test design (совместная проработка до кода — SPEC-0029 §6 / D6)

- **Behavior:** каждый эндпоинт агент-менеджмента и agent-self отвечает
  идентично до/после (паритет-тесты: существующие + новые на контракт
  DTO).
- **Boundaries:** пустые claim/inbox (пустые списки, отсутствие записей);
  чужой agent_id в параметрах чтения (политика владения — сейчас, вероятно,
  нет проверки: зафиксировать и покрыть явно — это ещё одна
  «пропущенная негативная граница»).
- **Conditions:** только identity+shared-импорты после чистки
  (grep-контракт из TASK-0177 — red на старом коде).
- **AC:** SPEC-0029 AC7 (нет импортов чужих моделей), AC8 (паритет).
- **Matrix:** unit — сервисы владельцев (позитив/негатив/граница чтения);
  integration — HTTP-паритет «до/после» по каждому роуту
  (обход списка маршрутов модуля); contract — импорт-гейт.

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | Инвентарь cross-context обращений (таблица в файл задачи) + characterization-тесты | — |
| 2 | Public-сервисы delivery/quality (red→green на их собственных тестах) | 1 |
| 3 | Перевод agent_endpoints/agent_self на сервисы (паритет) | 2, 0172 (гейты в тех же файлах) |
| 4 | Evidence: паритет + импорт-гейт зелёный | 3 |

## Inventory (Decomposition item 1 — done 2026-11-04)

Каждое foreign-context обращение + эндпоинт, которое оно обслуживает.
Кросс-контекстных JOIN'ов НЕТ (каждый запрос — одна таблица; batch по
`IN (ids)` — не JOIN) → разбивать нечего (Goal 3 закрыт проверкой SQL).

### `backend/app/identity/agent_endpoints.py` (foreign: delivery, quality)

| # | Import / query | Endpoint |
|---|---|---|
| 1 | `from app.delivery.models import AgentInboxEvent, ClarificationRequest, Task, TaskClaim` | module-level import |
| 2 | `from app.quality.models import Evidence, ReviewRound` | module-level import |
| 3 | `query(TaskClaim).filter(agent, state='completed').count()` | `GET /agents/{id}` (metrics) |
| 4 | `query(TaskClaim).filter(agent, state='expired').count()` | `GET /agents/{id}` (metrics) |
| 5 | `query(TaskClaim).filter(agent, state='active').first()` | `GET /agents/{id}` (active claim) |
| 6 | `db.get(Task, active_claim.task_id)` | `GET /agents/{id}` (task title) |
| 7 | lazy `from app.delivery.models import Heartbeat` + `query(Heartbeat).filter(claim_id).order_by(created_at desc).first()` | `GET /agents/{id}` (progress) |
| 8 | `query(TaskClaim.claimed_at).filter(agent).order_by(claimed_at desc).first()` | `GET /agents/{id}` (status/idle) |
| 9 | `query(TaskClaim).filter(agent).order_by(claimed_at desc).limit(100).all()` | `GET /agents/{agent_id}/claims` |
| 10 | `query(Task).filter(Task.id.in_(task_ids)).all()` | `GET /agents/{agent_id}/claims` (titles) |
| 11 | `query(AgentInboxEvent).filter(agent).order_by(created_at desc).limit(100).all()` | `GET /agents/{agent_id}/activity` |
| 12 | `query(Evidence).filter(created_by_id==agent).order_by(created_at desc).limit(100).all()` | `GET /agents/{agent_id}/evidence` |
| 13 | `query(ReviewRound).filter(reviewer_id==agent).order_by(created_at desc).limit(100).all()` | `GET /agents/{agent_id}/reviews` |
| 14 | `query(ClarificationRequest).filter(author_id==agent).order_by(created_at desc).limit(100).all()` | `GET /agents/{agent_id}/clarifications` |

### `backend/app/api/v1/agent_self.py` (foreign: delivery)

| # | Import / query | Endpoint |
|---|---|---|
| 15 | `from app.delivery.models import AgentInboxEvent, ClarificationRequest, TaskClaim` | module-level import |
| 16 | `query(TaskClaim).filter_by(agent, state='active').count()` | `GET /agent/me` (inbox_count) |
| 17 | `query(ClarificationRequest).filter(author_id, author_type='agent', state='open').count()` | `GET /agent/me` (inbox_count) |
| 18 | `query(AgentInboxEvent).filter_by(agent)[, is_read].order_by(created_at desc).limit(50).all()` | `GET /agent/inbox` |

### mcp `SessionLocal` fallbacks (item 4 inventory)

- `mcp/tools.py:10,897` — `call_tool(..., session=None)`: **все production-вызовы**
  передают сессию (`mcp/server.py:145` — единственная живая точка, всегда
  `session=session`). Без сессии зовут только regression-тесты
  `tests/test_mcp_bugfixes.py::TestCallToolSessionBug1` (2 теста, патчат
  `app.mcp.tools.SessionLocal` и требуют fallback) — файл вне allow-list.
- `mcp/context_pack.py:8,25` — `generate_project_context(session=None)` +
  `get_context_pack(project_id)` **вообще без сессии**: живой путь
  `resources/read` (JSON-RPC) и `GET /mcp/resources/{name}` →
  `mcp/resources.py::get_resource_content` → `get_context_pack(project_id)`
  — сессии туда не проброшена, а `mcp/resources.py`/`mcp/server.py` вне
  allow-list → fallback жив, baseline-записи остаются (deviation §4 ниже).

### Карта тестового покрытия (characterization)

| Endpoint | Существующие тесты | Решение |
|---|---|---|
| `GET /agents/{id}` (metrics) | `test_agent_detail.py` (metrics/idle/working+hb/404), `test_security_hardening.py` | покрыто — без изменений |
| `GET .../claims` | `test_agent_detail.py` (empty/after/404), `test_database_hardening.py` (batch) | покрыто — без изменений |
| `GET .../activity` | `test_agent_detail.py` (**только empty**) | ДОБАВИТЬ: with-data + чужой agent |
| `GET .../evidence` | **нет** | ДОБАВИТЬ: positive/empty/чужой/404 |
| `GET .../reviews` | **нет** | ДОБАВИТЬ: positive/empty/чужой/404 |
| `GET .../clarifications` | `test_agent_detail.py` (empty/404) | ДОБАВИТЬ: positive/чужой |
| `GET /agent/me` | `test_agent_self.py` (полное, incl. inbox_count 4 варианта) | покрыто — без изменений |
| `GET /agent/inbox` | `test_agent_self.py` (только empty/401) | ДОБАВИТЬ: events/unread_only/чужой agent |
| Ownership-граница чтения | нет | ДОБАВИТЬ: не-владелец читает GET-табы → 200 (текущая политика фиксируется явно, Test design) |
| Импорт-контракт (Conditions) | нет (boundary-gate есть, но red только через baseline) | ДОБАВИТЬ: assertion-level red на старом коде |
| Unit: сервисы владельцев | нет | ДОБАВИТЬ: `test_agent_read_services.py` (red → green) |

## Evidence (2026-11-04)

### Red → green

| Фаза | Команда | Результат |
|---|---|---|
| Red: сервисы | `pytest test_agent_read_services.py` | collection **ImportError**: `cannot import name 'AgentActivityService'` |
| Red: quality-чтения | `pytest test_agent_quality_tab_reads.py` | **4 failed** (AttributeError `list_by_creator`/`list_by_reviewer`) |
| Red: импорт-контракт | `pytest test_agent_endpoint_import_contract.py` | **3 failed** (foreign-model import'ы присутствуют) |
| Characterization (ДО рефакторинга) | `pytest test_agent_tabs_parity.py test_agent_self_inbox_parity.py` | **12 passed** (зафиксированы до движения кода) |
| Green: сервисы | `pytest test_agent_read_services.py test_agent_quality_tab_reads.py` | **21 passed** |
| Green: контракт + паритет + существующие | `pytest test_agent_endpoint_import_contract.py test_agent_tabs_parity.py test_agent_self_inbox_parity.py test_agent_detail.py test_agent_self.py test_database_hardening.py test_agent_surface_auth.py` | **52 passed** — существующие тесты БЕЗ изменений |

### Сервисы добавлены (сигнатуры)

`delivery/service.py::AgentActivityService(db: Session)` — 9 методов
(`count_claims(agent_id, *, state=None) -> int`,
`get_active_claim(agent_id) -> TaskClaim | None`,
`last_claimed_at(agent_id) -> datetime | None`,
`list_claims(agent_id, *, limit=100) -> list[TaskClaim]`,
`get_latest_heartbeat(claim_id) -> Heartbeat | None`,
`list_tasks_by_ids(task_ids: Sequence[str]) -> list[Task]`,
`list_inbox_events(agent_id, *, unread_only=False, limit=50) -> list[AgentInboxEvent]`,
`list_clarifications(author_id, *, limit=100) -> list[ClarificationRequest]`,
`count_clarifications(author_id, *, author_type=None, state=None) -> int`);
`quality/service.py::EvidenceService.list_by_creator(created_by_id, *, limit=100) -> list[Evidence]`;
`quality/service.py::ReviewRoundService.list_by_reviewer(reviewer_id, *, limit=100) -> list[ReviewRound]`.
Потребители: `agent_endpoints.py` (6 эндпоинтов) и `agent_self.py` (2)
импортируют только `app.delivery.service` / `app.quality.service`
(public surface, разрешён boundary-правилом). Прямых запросов к чужим
моделям в двух файлах — 0; кросс-контекстных JOIN'ов не было.

### Baseline-записи удалены (в том же коммите, что и код)

- `("identity/agent_endpoints.py", "foreign-model", "app.delivery.models")`
- `("identity/agent_endpoints.py", "foreign-model", "app.quality.models")`
- `("api/v1/agent_self.py", "foreign-model", "app.delivery.models")`
- Оставлены (НЕ мои): `agent_self → identity.agent_auth/agents`,
  `mcp/tools → delivery.models/lifecycle/workflow`, reporting-backlog и др.
- Gate `test_context_boundaries.py`: **25 passed** (exact-set: нет новых,
  нет stale).

### SessionLocal fallbacks — disposition (deviation, KEEP оба)

- `mcp/tools.py::call_tool` — production-путь (`mcp/server.py:145`) ВСЕГДА
  передаёт сессию; fallback мёртв в рантайме, но закреплён 2
  regression-тестами TASK-0038 (`test_mcp_bugfixes.py::TestCallToolSessionBug1`:
  `patch("app.mcp.tools.SessionLocal")` → AttributeError и явный assert
  fallback'а). Файл вне allow-list → удаление ломает full-suite гейт →
  fallback и baseline-запись ОСТАВЛЕНЫ. Вывод вынесен в отдельную задачу:
  пробросить/удалить вместе с обновлением тех тестов.
- `mcp/context_pack.py` — ЖИВОЙ путь без сессии: JSON-RPC `resources/read`
  и `GET /mcp/resources/{name}` → `resources.py::get_resource_content` →
  `get_context_pack(project_id)` без session; проброс требует
  `mcp/resources.py`/`mcp/server.py` (вне allow-list) → fallback и
  baseline-запись ОСТАВЛЕНЫ.

### Grep-контракт (AC7)

- `backend/app/identity` × `from app.{delivery,quality}.models` → **0 matches**.
- `backend/app/api/v1/agent_self.py` → **0 matches**.
- Deviation: `backend/app/api` целиком → 2 оставшихся match
  (`api/v1/delivery.py:5`, `api/v1/task_workflow.py:12`) — их
  foreign-model записи в baseline = `backlog`, файлы вне allow-list;
  трогать их нельзя (stale-гейт сломался бы) — это backlog-находка
  (см. Risks).

### Gates (последние строки)

```text
test_context_boundaries.py               → 25 passed
новые/затронутые endpoint-тесты (7 файлов) → 52 passed
unit-сервисы (2 файла)                    → 21 passed
FULL suite (--ignore sibling in-flight)   → 1505 passed, 0 failed,
                                            coverage 91.16% (≥80%)
ruff check backend                       → All checks passed!
ruff format <мои 10 файлов>              → 10 files left unchanged
mypy backend/app                         → Success: no issues in 119 files
```

### Отклонения (deviations)

1. Полный suite прогнан с `--ignore=test_surface_rate_limit.py
   test_surface_observability.py` — НЕОТСЛЕЖЕННЫЕ новые тесты параллельного
   TASK-0173 в mid-edit состоянии (их app-код ещё не ленден → collection
   ImportError `SurfaceRateLimit`; их observability-тесты дают 8 FAILED из
  за пересечение с правками `shared/logging|correlation`, которые НЕ мои).
   С этими двумя файлами: 8 failed; без них: 0 failed (оба подозрительных
   теста из моего прогона — `test_auth_enumeration`,
   `test_real_main_agent_surface_lifecycle` — позеленели в изоляции).
   Повторить full-suite после коммита TASK-0173.
2. Grep-контракт «весь `backend/app/api`» невыполним в рамках allow-list
   (см. Deviations в Grep-контракте) — доказан по identity + agent_self.
3. mcp `SessionLocal` fallback'ы НЕ удалены (см. disposition выше) —
   оба baseline-входа `session-local` честно остаются.

### §12 Multi-factor mini-analysis

- **Соответствие требованиям:** AC7 ✓ (grep-контракт + boundary-gate),
  AC8 ✓ (паритет 12 + 52 зелёных без правок тестов); Goals 1-4 ✓ (Goal 3:
  JOIN'ов не было — проверено инвентарём).
- **Архитектура/DDD:** чтение чужого контекста только через public
  service; новый `AgentActivityService` — в владельческом контексте,
  без новых импорт-паттернов (public surface = `service.py` — уже
  whitelisted TASK-0172); чистых DTO не вводил — контекст-конвенция
  сервисов возвращает rows (как `TaskService.get`), потребитель не
  импортирует модели.
- **Производительность:** те же single-table запросы + batch `IN`;
  метрики completed/expired = 2 count-запроса (как было); N+1-гейт
  (`test_agent_claims_batch_query`) зелёный.
- **Безопасность:** auth/ownership-семантика не тронута (поритетом
  зафиксировано: GET-табы — open reads для authenticated, agent-self —
  только свои строки; write-gates 403 не тронуты).
- **Надёжность/наблюдаемость:** поведение байт-в-байт (shape-тесты с
  точным набором ключей), ошибок не «проглатываем» — сервисы не
  обрабатывают исключений, эндпоинты не меняли error-поведение.
- **Тестируемость:** red зафиксирован (ImportError/AttributeError/
  assertions), unit (21) + characterization (12) + contract (3); минус —
  паритет «до» воспроизводится только history-коммитами (рефакторинг и
  тесты в одном PR), поэтому characterization закоммичен ДО кода.
- **Документация:** код-докстринги (public surface, parity-заметки)
  синхронизированы; правка docs/вне-allow-list не требовалась —
  нужные строки для SPEC-0029 §8 (mcp-fallback paragraph) и
  TASK-0177 (обновить inventory `api/v1/delivery.py`,
  `api/v1/task_workflow.py` + вынести mcp-входы) — см. Risks.

### Risks / next

- Сервисные методы переиспользуемы: mcp/tools.py (`get_agent_inbox`,
  request_clarification), reporting — кандидаты на будущие задачи, их
  foreign-model входы остаются в baseline как backlog.
- mcp `tools → delivery.models/lifecycle/workflow` и 2 `session-local`
  входа — backlog/deviation (см. disposition).
- Параллельный TASK-0173 может сократить `shared/rate_limit.py` redis-вход
  baseline — согласовать порядок правок `context_boundary_baseline.py`
  (файловый конфликт маловероятен: правки точечные).
