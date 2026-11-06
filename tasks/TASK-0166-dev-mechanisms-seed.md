# TASK-0166 — Dev seed: наполнить БД всеми механизмами и верифицировать компоненты

**Source:** Дмитрий 2026-10-31: «Наполнить БД данными так, чтобы убедиться, что
работают все механизмы и компоненты. Можно через БД, API или браузер.»
**Milestone:** dev-environment / verification (не релизный)
**Spec:** mini-spec (AC ниже)
**Points:** 5
**Status:** DONE (2026-10-31 — AC1-AC5 закрыты; verify 56/56, negative 11/11;
MR !102 merged → develop `1ffa7e7`, post-merge **develop #523 quality:gate
success** — `RCs: e2e=0 e2e_fe=0 chaos=0 security=0 perf=0`, exit 0, job 4023)

## Context

Dev-стек жив (`upcp-dev-*`, app `:38083`, db `:35435`, nginx `:3073`),
аккаунт `admin@dev.com` создан вручную. Каркас уже засеян (`scripts/seed_dev.py`):
3 projects, 4 components, 14 modules, 8 features, 36 tasks, 5 agents.
**Было пусто (0 строк):** claims, heartbeats, clarifications, DoD, evidence,
review rounds, notifications, notification channels, audit_event,
git provider/branches/commits, comments, subtasks, task_dependency,
membership, agent tokens.

Seed-скрипты устарели относительно контрактов API (DoD `title`→`name`,
claims требуют `X-Agent-Token` + статус `ready`, evidence требует
`created_by_id`, findings требуют `severity|category|message`, rate-limit
100 req/min без пейсинга).

**Домены без write-API** (SQL-бэкфил): `membership`, `audit_event`,
`git_branch`/`git_commit` (sync-методы без HTTP-роута), `task_dependency`,
backdating `created_at/updated_at` (analytics), stale `last_heartbeat_at`.

## Goals

1. Обновить seed-скрипты под актуальные контракты + env-конфиг + пейсинг.
2. Comprehensive seed всех механизмов через API.
3. SQL-бэкфил доменов без write-API.
4. Верификация read-back'ом каждого механизма + browser-pass.

## Acceptance Criteria

- [x] AC1: `seed_dev.py`/`seed_full.py` — env-конфиг, контракты исправлены
      (DoD `name` + PATCH-status, evidence `created_by_id`,
      findings `severity/category/message`, email-channel полный конфиг),
      пейсинг 90 req/min + 429-retry + auto-refresh в `seed_common.py`.
- [x] AC2: `seed_mechanisms.py` покрывает через API: agent tokens; полный
      жизненный цикл (11 статусов); claim/heartbeat/release; clarifications
      (blocking-open + answered); DoD passed/failed/pending; AC; evidence
      (agent_verified/human_accepted/rejected); review rounds
      (pending/in_progress/completed × reject|approve × human|agent) +
      findings; gate positive + negative; comments/subtasks/bulk/reports.
- [x] AC3: `seed_backfill.sql`: membership (owner), 25 audit_event
      (15 для project-страницы UPCP), 3 git branches, 6 commits,
      2 task_dependency, backdating 13 done-задач (8 недель истории),
      stale heartbeat в окно [7,15) мин.
- [x] AC4: `verify_seed.py` — **56/56 PASS, exit 0**: все 8 attention-секций
      непустые, 11/11 lifecycle-статусов, notifications 21 в bucket
      `default`, audit 15+export CSV, git, analytics (velocity 7 недель),
      channels, search, `/auth/me` organizations, `/health`, `/metrics`,
      SSE keepalive, MCP `tools/list` → 200.
- [x] AC5: negative paths **11/11**: claim cancelled→409, claim без
      токена→401, claim unknown→404, invalid transition→**422**
      (новый фикс, см. ниже), gate blocked→400, gate failed-DoD→400,
      complete failed-DoD→400, 4× unknown-resource→404.
      Rate-limit: 429 наблюдался и корректно ретраился (Retry-After).
- [x] Evidence: Verification ниже; PROJECT_STATUS синхронизирован.

## Bugfix, найденный в ходе AC5 (вне первоначального Out of scope)

Невалидный переход статуса через HTTP возвращал **500** (воспроизведено на
живом dev: `PATCH done→backlog` → `internal_error`). Причина:
`InvalidTransition` (plain Exception) не перехватывался на HTTP-границе.
Попутный аудит нашёл ещё 3 утечки в `task_workflow.py` (release, blocking
clarification create/answer).

**TDD-фикс:** `backend/tests/test_task_transition_api.py` (8 тестов,
red: `assert 500 == 422` ×4 → green: 8 passed); фикс в
`backend/app/api/v1/delivery.py` + `backend/app/api/v1/task_workflow.py`
→ **422** (консистентно с `bulk_update_tasks`). Полный прогон:
**1097 passed**, `ruff check backend` clean, `mypy backend/app` — 114 files,
no issues. На живой dev фикс доставлен `docker cp` + restart контейнера
(запечённый образ от 25.10 — эфемерно до следующего rebuild; в репо фикс
закоммичен).

## Verification (2026-10-31)

### Прогоны

```text
SEED_BASE=http://127.0.0.1:38083 SEED_EMAIL=admin@dev.com \
  .venv/bin/python scripts/seed_full.py         → exit 0, 67 ✓, 0 WARN
SEED_BASE=... .venv/bin/python scripts/seed_mechanisms.py
                                                → exit 0, 0 WARN,
                                                  negative 11/11
docker exec -i upcp-dev-db-1 psql ... < scripts/seed_backfill.sql
                                                → membership 1, audit 25,
                                                  branches 3, commits 6,
                                                  deps 2, backdated 13,
                                                  stale_claims 1
SEED_BASE=... .venv/bin/python scripts/verify_seed.py
                                                → 56/56 PASS, exit 0
```

### Read-back ключевых значений

| Механизм | Evidence |
|---|---|
| Attention (8 секций) | needs_review 2, open_questions 1, blocked 1, stale_claims 1, failed_dod 5, rejected 1, verdicts_waiting 3, low_health 2 |
| Lifecycle | 11/11 задач в ожидаемых статусах (ready/claimed/in_progress/blocked/needs_clarification/ready_for_review/changes_requested/cancelled/done/backlog) |
| Notifications | unread-count = **21** в bucket `default` (то, что читает колокольчик) |
| Quality stats | total_dod 24, passed 15, pass_rate 55.32% |
| Agent activity | 5 активных клеймов, qa-engineer flagged Stale |
| Reaper | `POST /internal/reaper/tick` → `{"stale":1,"released":0}` — stale-детект работает, claim жив (9 мин < 15 мин dead) |
| Analytics | velocity 7 недель непустых, health-history 30 дней |
| Audit | feed 10/10 (cap), UPCP-страница 15 событий, CSV export 200 |
| SSE | keepalive `: keepalive` получен |
| MCP | `tools/list` → 200, project_list в ответе |
| Browser | логин → дашборд: колокольчик 21, Needs Attention (4 карточки), Recent Activity (reaper-событие), Active Agents с прогресс-барами |

### Delivery

- 3 атомарных коммита → MR !102 (`3b2f507` fix 422, `ab04161` seed-скрипты,
  `30df961` docs) → merged, develop `1ffa7e7`.
- Post-merge CI: **develop #523 success**, `quality:gate` job 4023 —
  `RCs: e2e=0 e2e_fe=0 chaos=0 security=0 perf=0`, `quality gate exit: 0`.

### Multi-factor анализ (AGENTS §12)

- **Соответствие требованиям:** все 5 AC закрыты read-back'ом; browser-pass
  подтвердил UI-рендер.
- **Архитектура:** правки только на HTTP-границе (сервис/lifecycle не
  тронуты); SQL-бэкфил — отдельный файл с idempotent-guard'ами.
- **Надёжность:** 4 утечки InvalidTransition → 422 (фикс + регресс-тесты);
  seed-скрипты идемпотентны (reuse по title, ON CONFLICT, NOT EXISTS).
- **Производительность:** пейсинг под лимит — 429 не встречались в
  финальных прогонах (один ретрай во время прогона mechanisms).
- **Тестируемость:** verify_seed.py — повторяемый 56-check гейт;
  negative-expectations зашиты в скрипт (exit code = контракт).
- **Безопасность:** креды только через env; токены агентов — одноразовый
  raw из API, не логируются; секретов в коде нет.
- **Наблюдаемость:** наполнение через API прошло через event →
  notification → SSE-путь (21 уведомление), а не мимо сервисов.

### Наблюдения (follow-up, не чинилось в этой задаче)

1. **Нет write-API для audit_event** — Recent Activity и страницы аудита
   заполняются только SQL-бэкфилом (фронтовый `POST /audit-events` не
   существует на бэке — мёртвый клиентский код в `lib/api/audit.ts`).
2. **Git sync без HTTP-роута** — `sync_branches/sync_commits` недоступны
   извне (только сервис + SQL).
3. **Нет эндпоинта task_dependency** — модель есть, CRUD нет.
4. **Уведомления: bucket mismatch** — события пишут `user_id` из
   assignee/task, а фронт читает `default`; решается TASK-0164
   (notification contract). Seed пошёл через assignee_id="default".
5. **Reaper-шум для stale claims** — каждый тик (60с) публикует
   `claim.stale` повторно для тех же claims → дубли уведомлений/inbox
   событий между 5 и 15 минутами жизни stale-клейма.
6. **`TaskService.complete` минует `validate_transition`** — complete()
   ставит `done` без проверки state machine (обход из cancelled и т.п.).
   Minor, завести задачу.
7. Dev-контейнер `upcp-dev-app-1` запущен из CI-runner checkout
   (`/builds/.../docker-compose.stage.yml`, образ от 25.10) — код в нем
   запечён, `--reload` отсутствует. Фикс 422 доставлен docker cp;
   при следующем rebuild образа попадёт из репо.
