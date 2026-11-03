# TASK-0176 — Cross-context cleanup: agent_endpoints / agent_self без прямых запросов к чужим моделям

**Source:** SPEC-0029 §3.6 (S29.6), audit finding 9; AGENTS.md §5 (DDD)
**Milestone:** auth rework (SPEC-0029 batch)
**Spec:** SPEC-0029 §3.6, AC7
**Points:** 5
**Status:** PENDING (реализация не начата)

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
