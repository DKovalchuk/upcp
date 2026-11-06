# TASK-0164 — Notifications API contract: user_id bucket + envelope (verification, auth-sensitive)

**Source:** находки verification-агента TASK-0160 (2026-10-31): O1 (envelope)
и O4 (user_id) в отчёте по `backend/app/api/v1/notifications.py`
**Milestone:** Production hardening (queue)
**Spec:** mini-spec (AC ниже) — **чувствительная зона: API contract + auth**,
по AGENTS.md §10 эскалация перед реализацией
**Points:** 3
**Status:** pending

## Findings (evidence из TASK-0160 verification)

1. **O4 — возможный functional gap (auth-sensitive):** эндпоинты читают
   bucket `user_id="default"`, если `?user_id=` не передан; production-писатели
   (`app/reporting/trigger.py`) пишут `assignee_id`/`author_id`/`system` —
   никогда `"default"`; фронтенд REST-вызовы `user_id` не передают
   (`client.ts` добавляет только Authorization). Итог: колокольчик/список
   могут читать всегда пустой bucket. Дополнительно `user_id` — spoofable
   query-параметр (нет привязки к auth subject).
2. **O1 — envelope/пагинация:** `GET /notifications` возвращает только
   `{items}` без `{total, offset, limit}` (все прочие list-эндпоинты дают
   envelope); PRD §6.3 (`docs/prd/human-control-ux.md:135`) документирует
   `?unread=true&limit=50`, код принимает `unread_only` без `limit`.

## Goals

1. Проверить live-поведение: доходят ли реальные уведомления до
   фронтенда (bell/unread-count/list) в dev-стеке — воспроизвести
   сценарий «событие → trigger → GET list» с реальным пользователем.
2. Определить контракт: привязка bucket к auth subject (server-side
   `current_user` вместо spoofable query) vs явный `user_id` param.

## Acceptance Criteria

- [ ] AC1: воспроизведение подтверждает/опровергает gap (live-или интеграционный
      тест: trigger пишет assignee → GET list для этого пользователя).
- [ ] AC2: решение по контракту принято и задокументировано (AC → изменение
      эндпоинта/фронтенда; если требуется auth-привязка — Pro-review по §9).
- [ ] AC3: фикс покрыт red→green тестами (HTTP + фронтенд).
- [ ] AC4: envelope `{total, offset, limit}` + параметры `limit/offset`
      согласованы с PRD (или PRD поправлен); дефолтные значения совместимы
      с фронтендом.
- [ ] AC5: `docs/prd/human-control-ux.md` синхронизирован с фактическим API
      (методы, параметры).

## Stop conditions (AGENTS.md §10)

Изменение затрагивает auth/API contract — до реализации AC2: эскалация,
решение фиксируется до кода.

## Verification

_(заполняется)_
