# TASK-0168 — API surface registry + default-deny contract test

**Source:** SPEC-0028 §3.1 (S28.1); Dmitry 2026-11-02 («надо использовать
встроенное в FastAPI решение… хардкод путей — хрупкое решение»)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.1, AC1/AC2/AC3
**Points:** 3
**Status:** DONE (2026-11-02 — контракт-тест red→green, полный прогон 1102 passed)

## Context

Сейчас аутентификация «включается» строками путей
(`middleware.py:135`, `rate_limit_middleware.py:33`), а публичность —
runtime-словарём `PUBLIC_PATHS`. Классификация ручек должна стать
явным временем композиции + проверяемым контрактом. Это основа для
TASK-0169/0170 (blanket-зависимости на include_router) и для
перечислительного теста AC1 («неавторизованный запрос не выполняется
НИ на одной ручке» — сценарий, пропущенный в старой тестовой сьюте).

## Goals

1. `backend/app/api/registry.py`: `WEB_ROUTERS`, `AGENT_ROUTERS`,
   `PUBLIC_ROUTERS` + константы префиксов (`API_PREFIX="/api/v1"`,
   `MCP_PREFIX="/mcp"`) — единственный источник правды; `main.py`
   подключает роутеры через реестр (composition, не runtime-строки).
2. Contract-тест: каждая зарегистрированная ручка `app.routes`
   принадлежит ровно одной группе; ручки уровня `app` (health, metrics,
   docs/redoc/openapi) явно перечислены в `PUBLIC_ROUTERS`.
3. Мутирующий негатив: ручка, добавленная в роутер вне реестра → тест падает.

## Test design (совместная проработка до кода — SPEC-0028 §6 / D6)

- **Behavior:** классификация полная и взаимно-непересекающаяся; реестр —
  данные, а не логика маршрутизации.
- **Boundaries:** ручки уровня `app` (не в роутерах); `include_router`
  с несколькими префиксами; OPTIONS/CORS-ответы; mount `/mcp`.
- **Conditions:** auth пока НЕ включён (этап классификации) — тест
  проверяет принадлежность группам, а не наличие 401 (это AC1 → TASK-0169/0170).
- **AC:** SPEC-0028 AC3 (полная классификация), контракт «группы disjoint».
- **Matrix:** unit — сверка реестра vs `app.routes` (позитив: все ручки
  найдены; негатив: роутер выпущен → fail; негатив: ручка в двух группах →
  fail; boundary: ручка уровня `app` вне `PUBLIC_ROUTERS` → fail).

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | `registry.py` + перевод `main.py` на реестр (поведение не меняется) | — |
| 2 | Contract-тест классификации (red: реестра нет/неполон → green) | 1 |
| 3 | Evidence: полный прогон (реестр ≠ поведение — только структура) | 2 |

## Notes

- Реестр принципиально отличается от `PUBLIC_PATHS`: это объявление на
  этапе композиции, проверяемое контракт-тестом, а не runtime-словарь в
  middleware; в runtime строк путей в аутентификации не будет (D2).
- Не трогать логику middleware в этой задаче — только структура.

## Evidence (2026-11-02)

### Red → Green

```text
red:   ModuleNotFoundError: No module named 'app.api.registry' (collection error)
green: 5 passed — backend/tests/test_api_surface_registry.py
       (полнота классификации, disjoint-группы, префиксы-контракт,
        живость PUBLIC_APP_PATHS, mutation-негатив синтетического роута)
```

### Верификация

```text
auth-набор с мигрированным харнессом: 43 passed
  (test_api_surface_registry + test_auth_endpoints + test_logout_denylist +
   test_auth_middleware_protection + test_public_paths +
   test_auth_middleware_user_check)
полный прогон (CI-форма): 1102 passed, coverage 89.51% (gate 80%)
ruff check backend → All checks passed; ruff format --check → 251 formatted
mypy backend/app → Success: no issues found in 115 source files
```

### Находки/отклонения

- FastAPI 0.139.2 / starlette 1.3.1: `include_router` лениво кладёт
  `_IncludedRouter` в `app.routes` (не копии ручек, как в старых версиях) —
  классификация идёт через `original_router`; это зафиксировано в
  docstring `route_surface`.
- `/auth`-роутер сплитнут на `public_router` (setup/login/refresh) и
  `router` (me/logout/password): иначе blanket-зависимость веб-поверхности
  (TASK-0169) закрыла бы публичные ручки. Пути не изменились; тестовые
  харнесс-точки обновлены (test_auth_endpoints, test_logout_denylist ×2).
- `PUBLIC_APP_PATHS` дополнен `/docs/oauth2-redirect` (ранее не
  декларировался — контракт-тест его поймал).
- Классификация по D5 подтверждена grep'ом фронтенда: `/api/v1/workflow` и
  `/api/v1/agent-self` браузер не вызывает (agent-поверхность);
  `/api/v1/agents/*` — web (браузер вызывает, admin-менеджмент).

### Multi-factor анализ (AGENTS §12)

- **Соответствие требованиям:** AC задачи (полнота классификации,
  mutation-негатив, неизменность поведения) закрыты тестами выше; спеки
  утверждены Дмитрием 2026-11-02.
- **Архитектура:** классификация — данные композиции (единый реестр),
  runtime-строк нет; `main.py` потерял 19 include-строк; поведение API не
  изменилось (полный сьют без регрессий).
- **Производительность:** индексы строятся один раз при импорте,
  `route_surface` — O(1) lookup; порядок подключения роутеров сохранён
  по группам (перекрытий путей нет — конфликтов разрешения не существует).
- **Безопасность:** структурно закрывает класс finding 2/9 — роут вне
  реестра = падение контракт-теста, а не молчаливый unauth-роут;
  аутентификация переключается в TASK-0169/0170.
- **Надёжность:** fail-fast на импорте при пересечении групп
  (RuntimeError в `_build_indexes`).
- **Тестируемость:** `route_surface` проверяется на синтетических роутах
  (mutation-негатив без порчи прод-компонента).
- **Документация:** PROJECT_STATUS синхронизирован; статусы спек →
  APPROVED.
