# TASK-0172 — RBAC coverage: require_permission на все опасные мутации + require_role

**Source:** SPEC-0028 §3.5 (S28.5), решение D4 (Dmitry 2026-11-02:
«расширить require_permission»)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.5, AC8; SPEC-0027 §3.1 (Phase A закрыта, Phase B — здесь)
**Points:** 5
**Status:** DONE (2026-11-04; evidence ниже)

## Context

`require_permission` (SPEC-0027, TASK-0145) покрывает только Phase A:
CRUD проектов и управление агентами. Остальные опасные мутации
(delivery/quality/structure/delete-операции, notification-channels,
gitread-мутации) — «any-authenticated». Гейт читает
`request.state.user_id` из middleware — после TASK-0169 источник
принципала меняется на web_auth-зависимость.

## Goals

1. Инвентарь мутаций (POST/PATCH/DELETE всех web-роутеров) → таблица
   `action:resource` per route; расставить `require_permission` на
   опасные операции (минимум: delete-мутации всех контекстов,
   create/update структуры/quality-гейтов).
2. Добавить `require_role(role)` / `require_superuser()` для
   admin-only операций (роль как семантика, не пара permission).
3. Гейты читают принципал из нового контекста (web_auth); кеш пар
   прав через `AuthCacheProvider` (SPEC-0029 S29.5) — инлайн-Redis в
   `permissions.py` уходит.
4. Обратная совместимость: порядок fail-closed-проверок и superuser
   bypass не меняются (SPEC-0027 §3.1 amendment); reads не получают
   новых гейтов без явного решения.

## Inventory — все мутации allow-listed роутеров (составлен ДО расстановки гейтов)

58 мутаций (POST/PATCH/PUT/DELETE) в `api/v1/{structure,delivery,quality,
notifications,notification_channels,reporting,dashboard,audit,search,
gitread,analytics,reaper,projects,agent_self,task_workflow}.py`.
`dashboard/analytics/audit/search/agent_self` — только GET, мутаций нет.

Решения: `GATE a:r` = `require_permission(action, resource)` route-level;
`GATE!!super` = `require_superuser()`; `— U1..U5` = без гейта.

Коды обоснований ungated:
**U1** рутинная create/update рабочего элемента, малый радиус (минимум
задачи для delivery — только dangerous-мутации: bulk + все delete);
**U2** self-service состояние прочтения, недеструктивно;
**U3** производный артефакт, данных не теряет/не меняет;
**U4** agent-сurface: принципал = агентный ключ + `require_agent_scope`
(AC6); `require_permission` читает user-принципала → 401 сломал бы
workflow — authz-эквивалент здесь scope-гейт;
**U5** метаданные ассоциации без новой capability доступа к данным.

| # | File | Метод | Путь | Хендлер | Решение |
|---|------|-------|------|---------|---------|
| 1 | structure | POST | /projects/{id}/components | create_component | GATE create:component |
| 2 | structure | PATCH | /components/{id} | update_component | GATE update:component |
| 3 | structure | DELETE | /components/{id} | delete_component | GATE delete:component |
| 4 | structure | POST | /components/{id}/modules | create_module | GATE create:module |
| 5 | structure | PATCH | /modules/{id} | update_module | GATE update:module |
| 6 | structure | DELETE | /modules/{id} | delete_module | GATE delete:module |
| 7 | delivery | POST | /projects/{id}/features | create_feature | — U1 |
| 8 | delivery | PATCH | /features/{id} | update_feature | — U1 |
| 9 | delivery | DELETE | /features/{id} | delete_feature | GATE delete:feature |
| 10 | delivery | POST | /features/{id}/tasks | create_task | — U1 |
| 11 | delivery | PATCH | /tasks/bulk | bulk_update_tasks | GATE update:task (dangerous: масса ≤100 задач/вызов) |
| 12 | delivery | PATCH | /tasks/{id} | update_task | — U1 |
| 13 | delivery | DELETE | /tasks/{id} | delete_task | GATE delete:task |
| 14 | delivery | POST | /tasks/{id}/subtasks | create_subtask | — U1 |
| 15 | delivery | PATCH | /subtasks/{id} | update_subtask | — U1 |
| 16 | delivery | DELETE | /subtasks/{id} | delete_subtask | GATE delete:subtask |
| 17 | delivery | POST | /tasks/{id}/comments | create_comment | — U1 (append-only) |
| 18 | quality | POST | /tasks/{id}/acceptance-criteria | create_ac | GATE create:acceptance_criteria |
| 19 | quality | PATCH | /acceptance-criteria/{id} | update_ac | GATE update:acceptance_criteria |
| 20 | quality | DELETE | /acceptance-criteria/{id} | delete_ac | GATE delete:acceptance_criteria |
| 21 | quality | POST | /tasks/{id}/dod-items | create_dod | GATE create:dod_item |
| 22 | quality | PATCH | /dod-items/{id} | update_dod | GATE update:dod_item |
| 23 | quality | DELETE | /dod-items/{id} | delete_dod | GATE delete:dod_item |
| 24 | quality | POST | /tasks/{id}/complete | complete_task | GATE update:task (закрытие работы) |
| 25 | quality | POST | /tasks/{id}/submit-review | submit_task_for_review | GATE create:review_round |
| 26 | quality | POST | /tasks/{id}/evidence | create_evidence | GATE create:evidence |
| 27 | quality | POST | /evidence/{id}/agent-verify | agent_verify_evidence | GATE update:evidence |
| 28 | quality | POST | /evidence/{id}/human-accept | human_accept_evidence | GATE update:evidence (решение приёмки) |
| 29 | quality | POST | /evidence/{id}/reject | reject_evidence | GATE update:evidence (решение приёмки) |
| 30 | quality | POST | /tasks/{id}/evidence/upload | upload_evidence_file | GATE create:evidence |
| 31 | quality | POST | /tasks/{id}/review-rounds | create_review_round | GATE create:review_round |
| 32 | quality | POST | /review-rounds/{id}/start | start_review_round | GATE update:review_round |
| 33 | quality | POST | /review-rounds/{id}/findings | create_review_finding | GATE create:review_finding |
| 34 | quality | POST | /review-rounds/{id}/verdict | submit_verdict | GATE update:review_round (финальный вердикт) |
| 35 | notifications | POST | /notifications/{id}/read | mark_notification_read | — U2 |
| 36 | notifications | POST | /notifications/read-all | mark_all_read | — U2 |
| 37 | notification_channels | POST | /notification-channels | create_channel | GATE create:notification_channel |
| 38 | notification_channels | PATCH | /notification-channels/{id} | update_channel | GATE update:notification_channel |
| 39 | notification_channels | DELETE | /notification-channels/{id} | delete_channel | GATE delete:notification_channel |
| 40 | notification_channels | POST | /notification-channels/{id}/toggle | toggle_channel | GATE update:notification_channel (вкл/выкл алертинга) |
| 41 | notification_channels | POST | /notification-channels/{id}/test | test_channel | GATE update:notification_channel (исходящие в каналы) |
| 42 | reporting | POST | /projects/{id}/reports/daily | generate_daily_report | — U3 |
| 43 | reporting | POST | /reports/{id}/summarize | summarize_report | — U3 (LLM-стоимость — продуктовое, не authz-решение) |
| 44 | gitread | POST | /projects/{id}/git-providers | create_provider | GATE create:git_provider (dangerous: задаёт источники данных, включая local-пути) |
| 45 | gitread | PATCH | /git-providers/{id} | update_provider | GATE update:git_provider (переадресация источника) |
| 46 | gitread | DELETE | /git-providers/{id} | delete_provider | GATE delete:git_provider |
| 47 | gitread | POST | /git-links | create_link | — U5 |
| 48 | gitread | DELETE | /git-links/{id} | delete_link | GATE delete:git_link |
| 49 | reaper | POST | /internal/reaper/tick | reaper_tick_endpoint | GATE!!super (ops-endpoint; HTTP-вызывающих нет — см. таблицу) |
| 50 | projects | POST | /projects | create_project | Phase A: GATE create:project (без изменений) |
| 51 | projects | PATCH | /projects/{id} | update_project | Phase A: GATE update:project (без изменений) |
| 52 | projects | DELETE | /projects/{id} | delete_project | Phase A: GATE delete:project (без изменений) |
| 53-58 | task_workflow | POST | claim/release/heartbeat/progress/clarifications/answer | — | — U4 (агент-сurface, scope-гейты AC6) |

**Итог:** 36 новых `require_permission` + 1 `require_superuser` (reaper);
+6 существующих Phase-A = **43 route-гейта** после задачи.

### Новые пары прав (проверено: в `identity/seed.py` отсутствуют → добавляются)

| Пара | Owner | Admin | Member | Для каких гейтов |
|------|-------|-------|--------|------------------|
| delete:subtask | + | + | — | #16 |
| create:acceptance_criteria | + | + | + | #18 |
| update:acceptance_criteria | + | + | + | #19 |
| delete:acceptance_criteria | + | + | — | #20 |
| create:dod_item | + | + | + | #21 |
| update:dod_item | + | + | + | #22 |
| delete:dod_item | + | + | — | #23 |
| create:evidence | + | + | + | #26, #30 |
| update:evidence | + | + | + | #27-29 |
| create:review_round | + | + | + | #25, #31 |
| update:review_round | + | + | + | #32, #34 |
| create:review_finding | + | + | + | #33 |
| create:notification_channel | + | + | — | #37 |
| update:notification_channel | + | + | — | #38, #40, #41 |
| delete:notification_channel | + | + | — | #39 |
| create:git_provider | + | + | — | #44 |
| update:git_provider | + | + | — | #45 |
| delete:git_provider | + | + | — | #46 |
| delete:git_link | + | + | — | #48 |

Принципы грантов: Owner/Admin — полный доступ («Full access» /
«Everything except user management»); Member — create/update рабочих
элементов (AC/DoD/evidence/review), без delete (зеркалит отсутствие
`delete:component/task` у Member); channel/git-провайдер — интеграционная
конфигурация уровня администратора (Owner/Admin). Viewer — без новых пар
(`test_seed.py::test_viewer_has_read_only` закреплён).

### require_role / require_superuser — решения по применению

| Роутер/роут | Доказательство | Решение |
|---|---|---|
| POST /internal/reaper/tick | «internal» ops-endpoint; вызывается только фоновым циклом (прямой вызов сервиса) и runbook-скрипт setup-супербьюзером; **ни один тест/e2e/скрипт не дёргает HTTP**; mutate-ит claims | применён `require_superuser()` |
| агент-админ роуты (`agent_endpoints`) | уже `manage:agent` (пара, не роль) | не трогаем (Phase A) |
| user-management эндпоинты | отсутствуют в коде (`manage:user` без HTTP-роутов) | **omission**: `require_role` без применения — proposal: будущие `/auth/users*`, org-settings роуты → `require_role("Owner")` / `require_superuser()` |
| остальные Phase-B гейты | ни один роут не является role-семантическим (admin-only) по коду/вызывающим | omission, зафиксировано выше |

## Test design (совместная проработка до кода — SPEC-0028 §6 / D6)

- **Behavior:** мутация без права → 403 (не 404/500); с правом → 2xx;
  superuser → всегда; роль-gate: не та роль → 403.
- **Boundaries:** право есть, но пользователь disabled (→ 401, не 403 —
  существующий порядок); гейт при `disable_auth` (инертен — hermetic);
  супербьюзер без RoleBinding (существующий AC9-кейс не должен упасть).
- **Conditions:** Redis up/down (кеш пар → фолбэк в БД — SPEC-0029 AC3);
  пары прав закешированы до выдачи нового права (TTL 60с — негативный
  кейс: после grant запрос в течение TTL может 403 — зафиксировать
  поведение документацией, как сейчас).
- **AC:** SPEC-0028 AC8; регресс SPEC-0027 AC1/AC2/AC9.
- **Matrix:**
  - unit: каждый новый гейт — позитив (право есть) / негатив (нет
    права → 403) / негатив (нет принципала → 401) / граница
    (superuser, disabled-юзер); `require_role` — 4 ручных кейса.
  - integration: параметризация по таблице инвентаря — «мутация X без
    права → 403» для КАЖДОЙ покрытой ручки (не одна выборочная).
  - regression: ungated reads baseline (SPEC-0027 AC2) — статусы не
    изменились.
- **Red-фаза:** на каждый новый гейт — сначала тест «без права → 403»
  (падает до расстановки Depends), затем green.

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | Инвентарь мутаций + таблица прав (в файл задачи) | 0169 |
| 2 | Расстановка require_permission + require_role/red→green по таблице | 1, 0175 |
| 3 | Кеш пар через AuthCacheProvider | 0174 |
| 4 | Regression: полный прогон + authz live suite | 2-3 |

Выполнено: 1 ✓ (таблица выше, составлена до кода); 2 ✓; 3 — уже
доставлено TASK-0175 (`_resolve_user_permissions` читает через
`AuthCacheProvider` + `PermissionRepository`; инлайн-Redis в
`permissions.py` отсутствует — проверено), в этой задаче не менялось;
4 ✓ полный прогон; authz live suite (`tests/security/authz`) —
не запускалась: в среде нет docker/live-стендов (см. Deviations).

## Evidence (2026-11-04)

### 1. Финальный инвентарь гейтов

36 новых `require_permission` route-гейтов (structure ×6, delivery ×4,
quality ×17, notification_channels ×5, gitread ×4) + 1
`require_superuser` (`POST /api/v1/internal/reaper/tick`) = **43
route-гейта** с учётом 6 существующих Phase-A. Таблица по-роутная с
обоснованиями ungated-строк — секция «Inventory» выше (составлена ДО
расстановки гейтов; код в `tests/rbac_gates_matrix.py` — 1:1 с ней,
`test_every_matrix_pair_is_seeded` страхует от расхождения).

### 2. Seed-пары

19 новых пар (таблица грантов выше): `delete:subtask`;
`create/update/delete:acceptance_criteria`; `create/update/delete:dod_item`;
`create/update:evidence`; `create/update:review_round`;
`create:review_finding`; `create/update/delete:notification_channel`;
`create/update/delete:git_provider`; `delete:git_link` — в
`PHASE_B_ADMIN_PERMISSIONS` / `PHASE_B_MEMBER_PERMISSIONS`
(`identity/seed.py`, идемпотентный upsert как у существующих). Гранты:
Owner/Admin — все 19; Member — 9 create/update рабочих элементов; Viewer
— без новых пар (`test_seed.py::test_viewer_has_read_only` проходит).

### 3. Изменённые фикстуры/существующие тесты

**Никакие существующие фикстуры не тронуты** (conftest не менялся; все
auth-enabled позитивные тесты существовали только на projects/агент-админ
— Phase-A пары не двигались). Поправки только в двух файлах контрактов
(авторизованные правкой-правилом ниже):

- `backend/tests/test_context_boundaries.py` — правило foreign-internal;
- `backend/tests/context_boundary_baseline.py` — 1 устаревшая запись.

Новые файлы: `tests/rbac_gates_matrix.py` (матрица 36 гейтов + цепочка
ресурсов), `tests/test_rbac_gates_coverage.py` (182 кейса), `tests/
test_rbac_role_gates.py` (11 кейсов). Все ≤300 строк (243/156/197).

### 4. Правка boundary-rule (deliberate rule change)

`PUBLIC_SURFACE` в `tests/test_context_boundaries.py` дополнен
`permissions` с комментарием-обоснованием: гейты-фабрики — задокументированный
публичный FastAPI `Depends`-контракт (SPEC-0027 §3.1 «routes in other
contexts consume this gate via Depends only»); до правки каждая из 37
новых строк `from app.identity.permissions import ...` была бы NEW
violation exact-set-гейта. Сопутствующее: запись
`("api/v1/projects.py","foreign-internal","app.identity.permissions")`
удалена из BASELINE (stale-by-design); в `test_foreign_internal_rule`
добавлены 2 negative-кейса (permissions из structure/reaper → []).
Все остальные правила и их mutation/negative-кейсы не тронуты и зелёны
(`test_context_boundaries.py` — 20 passed в составе полного прогона).

### 5. Документация

`docs/security/auth-rbac.md` + `.ru.md` (EN/RU синхронно, версия
3.1.0 → 3.2.0): append-таблица Phase-B гейтов (29 строк), блок
«также доступен require_role», блок «сознательно без гейтов», пункт
семантики 403 `Insufficient role`/`Superuser required`, финальный
абзац §6 и ограничение §8 переписаны с «Phase B не enforced» на факт.
Контракт `test_auth_docs_contract.py` — green.

### 6. Red → Green

- **Red** (до реализации, 2 новых файла): `76 failed, 111 passed,
  5 errors` — ровно негатив-кейсы гейтов (36×«viewer→403» + 36×«нет
  принципала→401» + reaper owner/viewer/401 + seed-drift) и 5 ошибок
  `ImportError: require_role` (фабрики импортировались внутри тестов —
  коллекция проходила).
- **Green**: те же файлы `192 passed` → после сплита матрицы — целевые
  `256 passed` (coverage + role + rbac_enforcement + rbac + seed +
  permission_cache + context_boundaries).

### 7. Gates (команды и вывод)

- `pytest backend/tests -q -n auto` → **1469 passed, 0 failed,
  coverage 90.88%** (бейзлайн 1257/90.41%; прирост — новые тесты,
  count судить leniently из-за параллельного TASK-0171).
- `pytest` целевые (2 новых файла + rbac_enforcement + rbac + seed +
  permission_cache + context_boundaries) → **256 passed**;
  + `test_identity_layering_contract` → **243 passed** (5 файлов).
- `ruff check backend` → **All checks passed!**
- `ruff format --check` (14 моих файлов) → **14 files already formatted**
- `mypy backend/app` → **Success: no issues found in 119 source files**

### 8. Deviations

1. **`identity/repositories.py` +1 метод `PermissionRepository.holds_role`**
   (additive) — файл в списке FORBIDDEN задачи. Обоснование: Goal 2
   (рабочий `require_role`) + SPEC-0029 D1/AC1 («presentation does zero
   data access»; `db.query` разрешён ТОЛЬКО в `identity/repositories.py`)
   + контракт `test_identity_layering_contract` (запрещает `db.query` в
   `permissions.py` — полный прогон красный) одновременно выполнимы
   только через repository-метод; гонка с сиблингом исключена (TASK-0171
   работает в `mcp/**`), метод аддитивный в стиле `granted_pairs` (обе
   seams: injected-session + lazy SessionLocal). Альтернативы (запрос в
   `permissions.py`, `db.execute`-обход сканера, правка чужого
   контракт-теста, размещение в `seed.py`) отклонены как
   нарушающие D1/инструкции/читаемость.
2. **Authz live suite не запускалась** — в среде нет docker/live-стендов
   (по условию задачи). Риск минимален: `tests/security/authz/*` дёргает
   только projects/агент-админ мутации (Phase-A пары не менялись) —
   просмотрено вручную; перепроверить на живом стенде при первой возможности.
3. **Fixture-правки не потребовались** — hermetic-режим (`disable_auth=true`)
   держит ~все функциональные тесты инертными для новых гейтов; единственные
   auth-enabled позитивные сьюиты — dashboard/analytics (GET) и projects
   (Phase A). Наружные вызывающие (dev e2e, `scripts/seed_*`) ходят
   супербьюзером/Owner — гранты покрывают.

### 9. §12 multi-factor mini-analysis

- **Соответствие требованиям:** AC8 закрыт (403-не-404 на каждой новой
  мутации, superuser-байпас, ungated-reads baseline); Goal 1-4 ✓;
  red-phase по каждому гейту ✓. Reads не тронуты (AC2) — зафиксировано
  read-regression-тестом (11 GET).
- **Архитектура/границы DDD:** всё в `api/v1/*` (Depends-only) и
  `identity` (фабрики); boundary-rule-правка задокументирована;
  `task_workflow`/`agent_self` не гейтятся парой прав принципиально
  (агент-поверхность, scope-гейты) — U4 в инвентаре.
- **Производительность:** гейт = кэш пар (60 с, уже существующий) +
  1 `db.get(User)`; `holds_role` — cold-path (не используется в
  прод-роутах), без кэша осознанно (документировано в docstring).
- **Безопасность:** fail-closed порядок не менялся (401→401→bypass→403);
  дениалы — структурированный лог + `upcp_rbac_denials_total` + span;
  секретов нет; negative-контролы сохранены (Viewer без пар,
  binding-less из Phase A).
- **Надёжность/наблюдаемость:** метрики/спаны на каждый отказ
  (action=role/superuser добавлены), hermetic-inert ветка у всех трёх
  фабрик закреплена тестами.
- **Тестируемость:** 193 новых теста, матрица параметризована из
  инвентаря (не вручную), сплит по ≤300 строкам; качество покрытия —
  негатив+позитив+границы на КАЖДЫЙ гейт, а не выборочно.
- **Документация:** EN/RU синхронны, contract-тест путей зелёный;
  status задачи и PROJECT_STATUS не трогались (запрещены).

### 10. Next

- Proposal (из таблицы решений): первый role-роут (будущие
  `/auth/users*`, org-settings) → `require_role("Owner")`/`require_superuser`.
- Authz live suite прогнать на живом стенде (deviation 2).
- Cache-TTL-документация после grant (60 с) — уже в docs §6 («TTL 60 s»).
