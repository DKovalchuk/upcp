# TASK-0177 — Context-boundary contract test: автоматический гейт на границы DDD

**Source:** SPEC-0029 §3.7 (S29.7), audit finding 9 (аудиты объявляли
«no cross-context violations», пока нарушения были в коде)
**Milestone:** auth rework (SPEC-0029 batch)
**Spec:** SPEC-0029 §3.7, AC7
**Points:** 3
**Status:** DONE (2026-11-02 — контракт-гейт pytest+stdlib ast: 4 правила,
baseline 64 exact-entries, red→green + live-мутация; все гейты зелёные)

## Context

Границы контекстов (AGENTS §5) ничем не контролируются: ни
import-linter, ни contract-тестов. Ручные аудиты дважды дали ложный
«чисто» (`AUDIT_M16_COMPREHENSIVE.md:33`). Нужен автоматический гейт,
падающий в CI.

## Goals

1. Contract-тест границ импортов (варианты выбрать в задаче:
   `import-linter` как lint-стадия либо pytest AST/grep-тест —
   предпочтение pytest-варианту, если импорт-linter не заведён в CI:
   минимум новой инфраструктуры, работает в существующем гейте):
   - контекст импортирует `app.<context>` только: `shared` + свой +
     публичные поверхности других контекстов (`service`, `schemas`,
     `dependencies`-контракты — whitelist модулей);
   - модели чужих контекстов (`<ctx>.models`) — запрещены вне владельца
     (кроме явного whitelist, если миграция/seed требуют);
   - `SessionLocal` вне `shared` + `identity/repositories.py` → fail
     (расширяется по мере репликации паттерна);
   - redis-вызовы вне `shared/redis.py` + провайдеров → fail (пока —
     identity-провайдер; denylist/rate-limit — зафиксировать как
     временный whitelist с задачами на вынос).
2. Белый список — минимальный и задокументированный; каждое исключение
   — с комментарием-обоснованием и ссылкой на задачу.
3. Мутирующий контроль: нарушение, внесённое специально в тесте, гейт
   ловит (валидация гейта — обязательная часть AC).

## Test design (совместная проработка до кода — SPEC-0029 §6 / D6)

- **Behavior:** чистый код → гейт зелёный; импорт `app.delivery.models`
  из identity → red.
- **Boundaries:** тесты сами (`backend/tests`) — вне правил или под
  правилами? (решение: тестам разрешён любой импорт — они и ловят
  нарушения); `conftest`-фикстуры; legacy-исключения (что уже есть —
  инвентарь в задаче).
- **Conditions:** запуск в CI (стадия lint/test) и локально одной командой.
- **AC:** SPEC-0029 AC7; AC — валидация гейта (п.3).
- **Matrix:** unit — сам парсер/правила (позитив: легальный импорт;
  негатив ×4: чужая модель, чужой internal-модуль, SessionLocal вне
  whitelist, redis вне whitelist); интеграционный — прогон по всему
  `backend/app` (сейчас: TASK-0176 ещё не закрыт → гейт стартует в
  режиме «известный baseline» и переходит в strict после 0176 —
  решение о strict-переключении зафиксировать в задаче).

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | Инвентарь текущих нарушений (baseline-список в файл задачи) | — |
| 2 | Выбор механизма (pytest vs import-linter) + реализация гейта | 1 |
| 3 | Валидация гейта мутирующим тестом + подключение к CI | 2 |
| 4 | Strict-переключение после TASK-0176 | 0176, 3 |

## Evidence (2026-11-02)

### Механизм: pytest + stdlib `ast` — почему не import-linter

- import-linter не установлен и не заведён в CI → новая зависимость + новая
  стадия; задача новые зависимости запрещает. pytest уже гейтится
  (`.gitlab-ci.yml:165`, `pytest backend/tests -q -n auto`) — контракт-тест
  работает в существующем гейте без инфраструктуры (goal 1, вариант-предпочтение
  самой задачи).
- grep отклонён: ненадёжен на многострочных/вложенных (function-level,
  `TYPE_CHECKING`) импортах. AST-парсинг точен и даёт pure-функции над
  source-text → unit-тесты с синтетическими сниппетами (AC мутация) без
  изменения прод-кода.
- Код: `backend/tests/test_context_boundaries.py` (правила `_context_of`,
  `_foreign_model_imports`, `_foreign_internal_imports`, `_sessionlocal_refs`,
  `_redis_refs`, `_scan`; 23 теста) + `backend/tests/context_boundary_baseline.py`
  (таблица baseline). Zero новых зависимостей, TEST-ONLY.

### Baseline — 64 exact (file, rule, module) entries / 30 files

Никаких глоб: новое нарушение не покрыто → fail; убранное нарушение →
stale-запись → fail (обе стороны set-равенства). Ref-распределение:
backlog 46, «—» (структурно) 7, TASK-0176 ×5, TASK-0169 ×2, TASK-0174 ×2,
TASK-0175 ×1, TASK-0173 ×1.

| # | File | Rule | Module | Reason | Task ref |
|---|------|------|--------|--------|----------|
| 1 | `main.py` | foreign-internal | `app.api.registry` | composition root wires registry | — |
| 2 | `main.py` | foreign-internal | `app.delivery.stale_reaper` | composition root starts reaper | — |
| 3 | `main.py` | foreign-internal | `app.identity.middleware` | composition root adds AuthMiddleware | TASK-0169 |
| 4 | `main.py` | session-local | `SessionLocal` | root passes SessionLocal to reaper loop | — |
| 5 | `main.py` | redis | `app.shared.redis` | root health probe (check_redis_health) | — |
| 6 | `api/registry.py` | foreign-internal | `app.identity.agent_endpoints` | registry assembles context routers | — |
| 7 | `api/registry.py` | foreign-internal | `app.identity.endpoints` | registry assembles context routers | — |
| 8 | `api/registry.py` | foreign-internal | `app.mcp.server` | registry assembles context routers | — |
| 9 | `api/v1/agent_self.py` | foreign-model | `app.delivery.models` | agent-self queries delivery models (audit finding 9) | TASK-0176 |
| 10 | `api/v1/agent_self.py` | foreign-internal | `app.identity.agent_auth` | consumes agent-auth dep module (not public surface) | backlog |
| 11 | `api/v1/agent_self.py` | foreign-internal | `app.identity.agents` | imports Agent/AgentToken carrier module | backlog |
| 12 | `api/v1/analytics.py` | foreign-internal | `app.reporting.analytics` | AnalyticsService outside reporting public surface | backlog |
| 13 | `api/v1/dashboard.py` | foreign-model | `app.projects.models` | dashboard endpoint queries project model directly | backlog |
| 14 | `api/v1/dashboard.py` | foreign-internal | `app.reporting.attention` | attention service outside reporting public surface | backlog |
| 15 | `api/v1/dashboard.py` | foreign-internal | `app.reporting.dashboard` | dashboard service outside reporting public surface | backlog |
| 16 | `api/v1/dashboard.py` | foreign-internal | `app.reporting.portfolio` | portfolio service outside reporting public surface | backlog |
| 17 | `api/v1/delivery.py` | foreign-model | `app.delivery.models` | endpoint types against owner-context models | backlog |
| 18 | `api/v1/delivery.py` | foreign-internal | `app.delivery.lifecycle` | endpoint validates transitions via lifecycle | backlog |
| 19 | `api/v1/notification_channels.py` | foreign-model | `app.reporting.models` | endpoint queries reporting models directly | backlog |
| 20 | `api/v1/notification_channels.py` | foreign-internal | `app.reporting.channel_service` | ChannelService outside public surface | backlog |
| 21 | `api/v1/notifications.py` | foreign-internal | `app.reporting.sse` | endpoint consumes SSE manager directly | backlog |
| 22 | `api/v1/projects.py` | foreign-internal | `app.identity.permissions` | endpoint consumes RBAC gate (internal module) | backlog |
| 23 | `api/v1/reaper.py` | foreign-internal | `app.delivery.stale_reaper` | endpoint drives reaper tick directly | backlog |
| 24 | `api/v1/reporting.py` | foreign-model | `app.reporting.models` | endpoint types against owner-context models | backlog |
| 25 | `api/v1/reporting.py` | foreign-internal | `app.llm.gateway` | endpoint builds LLM gateway directly | backlog |
| 26 | `api/v1/reporting.py` | foreign-internal | `app.llm.redaction` | endpoint builds redactor directly | backlog |
| 27 | `api/v1/structure.py` | foreign-model | `app.structure.models` | endpoint types against owner-context models | backlog |
| 28 | `api/v1/task_workflow.py` | foreign-model | `app.delivery.models` | endpoint types against owner-context models | backlog |
| 29 | `api/v1/task_workflow.py` | foreign-internal | `app.delivery.lifecycle` | endpoint validates transitions via lifecycle | backlog |
| 30 | `api/v1/task_workflow.py` | foreign-internal | `app.delivery.workflow` | endpoint drives WorkflowService directly | backlog |
| 31 | `api/v1/task_workflow.py` | foreign-internal | `app.identity.agent_auth` | consumes agent-auth dep module (not public surface) | backlog |
| 32 | `reporting/analytics.py` | foreign-model | `app.delivery.models` | reporting aggregates via direct model reads | backlog |
| 33 | `reporting/attention.py` | foreign-model | `app.delivery.models` | attention dashboard reads delivery models directly | backlog |
| 34 | `reporting/attention.py` | foreign-model | `app.projects.models` | attention dashboard reads project models directly | backlog |
| 35 | `reporting/attention.py` | foreign-model | `app.quality.models` | attention dashboard reads quality models directly | backlog |
| 36 | `reporting/dashboard.py` | foreign-model | `app.audit.models` | dashboard reads audit models directly | backlog |
| 37 | `reporting/dashboard.py` | foreign-model | `app.delivery.models` | dashboard reads delivery models directly | backlog |
| 38 | `reporting/dashboard.py` | foreign-model | `app.projects.models` | dashboard reads project models directly | backlog |
| 39 | `reporting/dashboard.py` | foreign-internal | `app.identity.agents` | dashboard reads identity Agent via agents.py | backlog |
| 40 | `reporting/portfolio.py` | foreign-model | `app.delivery.models` | portfolio reads delivery models directly | backlog |
| 41 | `reporting/portfolio.py` | foreign-model | `app.projects.models` | portfolio reads project models directly | backlog |
| 42 | `reporting/service.py` | foreign-model | `app.delivery.models` | reporting service reads delivery models directly | backlog |
| 43 | `reporting/service.py` | foreign-model | `app.projects.models` | reporting service reads project models directly | backlog |
| 44 | `reporting/trigger.py` | foreign-model | `app.delivery.models` | trigger reads delivery models directly | backlog |
| 45 | `mcp/context_pack.py` | session-local | `SessionLocal` | SessionLocal fallback when caller injects none | TASK-0176 |
| 46 | `mcp/tools.py` | foreign-model | `app.delivery.models` | mcp tools read delivery models directly | backlog |
| 47 | `mcp/tools.py` | foreign-internal | `app.delivery.lifecycle` | mcp tools drive delivery lifecycle directly | backlog |
| 48 | `mcp/tools.py` | foreign-internal | `app.delivery.workflow` | mcp tools drive delivery workflow directly | backlog |
| 49 | `mcp/tools.py` | session-local | `SessionLocal` | SessionLocal fallback when caller injects none | TASK-0176 |
| 50 | `search/service.py` | foreign-model | `app.delivery.models` | search aggregates via direct model reads | backlog |
| 51 | `search/service.py` | foreign-model | `app.projects.models` | search aggregates via direct model reads | backlog |
| 52 | `identity/agent_endpoints.py` | foreign-model | `app.delivery.models` | identity routes query delivery models (audit finding 9) | TASK-0176 |
| 53 | `identity/agent_endpoints.py` | foreign-model | `app.quality.models` | identity routes query quality models (audit finding 9) | TASK-0176 |
| 54 | `identity/denylist.py` | redis | `app.shared.redis` | denylist caches inline; auth-path redis -> AuthCacheProvider | TASK-0174 |
| 55 | `identity/middleware.py` | session-local | `SessionLocal` | middleware queries DB directly; AuthMiddleware retired | TASK-0169 |
| 56 | `identity/middleware.py` | redis | `app.shared.redis` | subject-state cache inline; -> AuthCacheProvider | TASK-0174 |
| 57 | `identity/permissions.py` | redis | `app.shared.redis` | permission cache inline; -> AuthCacheProvider | TASK-0175 |
| 58 | `delivery/service.py` | foreign-model | `app.quality.models` | delivery reads quality DoD models directly | backlog |
| 59 | `quality/service.py` | foreign-model | `app.delivery.models` | quality reads delivery models directly | backlog |
| 60 | `quality/service.py` | foreign-model | `app.projects.models` | quality reads project models directly | backlog |
| 61 | `quality/service.py` | foreign-internal | `app.delivery.lifecycle` | quality validates delivery transitions | backlog |
| 62 | `shared/event_setup.py` | foreign-internal | `app.reporting.sse` | shared wires reporting consumers (backward dep) | backlog |
| 63 | `shared/event_setup.py` | foreign-internal | `app.reporting.trigger` | shared wires reporting consumers (backward dep) | backlog |
| 64 | `shared/rate_limit.py` | redis | `app.shared.redis` | rate-limiter consumes client directly; provider move unowned | TASK-0173 |

Правила по количеству: foreign-internal 28, foreign-model 27, redis 5,
session-local 4. Известные из задачи записи (agent_endpoints, agent_self,
mcp SessionLocal, redis denylist/permissions/rate-limit) подтверждены;
**остальные — результат инвентаризации и становятся findings** (см. отчёт):
mcp/tools delivery-импорты, cross-context чтение в reporting/quality/
delivery/search, api/v1 прямые model-импорты (6 файлов), shared→reporting
backward-зависимость, SessionLocal в main/middleware, redis в main.

### Red → Green

- **Red** (тесты написаны первыми, правил ещё нет):
  `22 failed, 1 passed, 1 warning in 0.71s`;
  причина — `NameError: name '_foreign_model_imports' is not defined`
  (по тесту на каждое правило).
- **Green** (правила реализованы): `23 passed, 1 warning in 0.94s` —
  baseline совпал с реальным деревом с первого прогона (нет новых, нет stale).
- **Live-мутация (AC, гейт end-to-end):** в `identity/seed.py` добавлен
  `from app.gitread.models import GitLink` → гейт красный с точным ключом:
  `NEW context-boundary violations ... [('identity/seed.py', 'foreign-model', 'app.gitread.models')]`
  → файл откачен → снова зелёный.
- **Mutation unit-тесты:** `test_scan_attributes_each_violation_to_its_rule`
  (один синтетический модуль → все 4 правила) и
  `test_new_violation_is_not_covered_by_baseline` (свежий violation
  isdisjoint с BASELINE — глоб-записи не могут спрятать новое нарушение).

### Гейты (последние строки)

- targeted: `23 passed, 1 warning in 0.87s`
- full suite: `1172 passed, 195 warnings in 22.91s` (0 failed; расклад:
  1102 baseline + 23 новых + 47 незакоммиченных тестов параллельной
  TASK-0174 в этом же checkout — collect-only проверено)
- `ruff check backend` → `All checks passed!`
- `ruff format --check backend` → `261 files already formatted`
  (формат применён к обоим новым файлам)
- `mypy backend/app` → `Success: no issues found in 119 source files`

### Отклонения (deviations)

1. **Два файла вместо одного** (разрешённое деление, >300 строк): CI гоняет
   `ruff format --check` — формат разворачивает dict-записи baseline по 4
   строки (~530 строк в одном файле). Baseline вынесен в
   `context_boundary_baseline.py` (модуль данных, pytest его не собирает);
   все тесты и правила остались в `test_context_boundaries.py` → целевая
   гейт-команда TASK-0177 работает как написана. Итог: 249 и 262 строки.
2. **Рефы без владельца.** Утверждение задачи «rate-limit уходит в провайдер
   в более поздних задачах батча» не подтвердилось: 0174/0175/0176 redis из
   `shared/rate_limit.py` не выносят (0173 — только policy) → запись №64:
   ref `TASK-0173` с честным reason «provider move unowned» (gap в отчёте).
   denylist → TASK-0174 (S29.2 «единственный redis в auth-пути»); 46
   записей `backlog` — честный факт «нарушение без задачи».
3. **Разделение правил:** `.models` считается только rule 1, rule 2 их
   пропускает — одно нарушение не дублируется в baseline дважды.
4. **Лимитация правила:** `from app.<ctx> import <submodule>` (len==2, не
   models) трактуется как `__init__`-поверхность; в дереве таких импортов
   нет (проверено). Модели в модулях не-`.models` (`identity.agents`,
   `identity.rbac`) ловит rule 2 как internal, а не rule 1 — осознанно по
   формулировке правила.

### Multi-factor analysis (AGENTS §12)

- **Соответствие требованиям:** 4 правила задачи ✓; AC7 (contract green) ✓;
  AC-мутация ✓ (unit + live); baseline exact, без глобов ✓; красный до
  реализации ✓; TEST-ONLY, zero deps ✓.
- **Архитектура:** правила — чистые функции `(source, path) → violations`,
  тестируемые на синтетике; тесты вне правил (решение D6); DDD-границы
  теперь исполняемы, а не декларативны.
- **Производительность:** один AST-проход на файл, гейт 0.9s; полный
  прогон не замедлен (22.9s).
- **Безопасность:** секретов нет; исходники читаются, app не исполняется;
  гейт усиливает DDD-изоляцию (защита от дрейфа границ).
- **Надёжность/наблюдаемость:** SyntaxError падает явно (не глотается);
  обе стороны set-равенства; сообщения об ошибках содержат точные ключи
  (file/rule/module) и инструкцию (fix | document | remove stale).
- **Тестируемость/качество тестов:** по каждому правилу позитив + негатив +
  граница (17 parametrize-кейсов + 6 сценарных, включая whitelist-формы,
  docstring-границу, package-surface); интеграционный гейт по дереву;
  live-мутация. Unit одинаково важна и после правок baseline.
- **Риски:** (a) координация — 0169/0174/0175/0176, убравшие нарушения,
  обязаны убрать свои baseline-иначе stale-fail (это намеренный дизайн,
  strict-переключение п.4 Decomposition = обновление baseline в 0176);
  (b) параллельный агент TASK-0174 пишет в тот же checkout — полный прогон
  пересчитан (1102+23+47); (c) новые импорт-формы len==2 — зафиксировано как
  лимитация.
- **Документация:** файл задачи дополнен; прод-доков не затронуто (scope).

### Files changed

- `backend/tests/test_context_boundaries.py` (new, 249)
- `backend/tests/context_boundary_baseline.py` (new, 262)
- `tasks/TASK-0177-context-boundary-contract.md` (status + evidence)
