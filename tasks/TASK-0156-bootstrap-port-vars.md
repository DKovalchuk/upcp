# TASK-0156 — Bootstrap scaffold port-var modernization (parent: TASK-0119 follow-up)

**Parent:** TASK-0119 (port externalization — follow-up: «`bootstrap_upcp.py`
scaffold templates still use legacy names (internally consistent — separate
modernization task)»; PROJECT_STATUS queue item; контракт-память
`task-0119-port-contract`: **Bootstrap scaffolds must emit `UPCP_PORT_*`
instead of legacy `UPCP_HTTP_PORT`-style names**)
**Milestone:** Этап 4 (production hardening + хвосты) — **последний item**
**Spec:** mini-spec по контракту TASK-0119 + docs/11 корневого проекта
**Points:** 2
**Status:** DONE (closed 2026-10-25)

## Objective

Привести порт-переменные генерируемых скрафтолдером-шаблонов к
каноническому префиксу `UPCP_PORT_*`, сохранив дефолтные значения и
внутреннюю согласованность генерации.

## Investigation (2026-10-25, evidence)

- Легаси-инвентарь `bootstrap_upcp.py`: **14 вхождений / 5 имён**
  (единственный реальный файл с легаси; упоминания в PROJECT_STATUS/
  TASK-0119 — исторические описания, не тронуты):

  | Легаси-имя | Где | Каноникал |
  |---|---|---|
  | `UPCP_HTTP_PORT` | docs/11, .env.example, compose (backend) | `UPCP_PORT_BACKEND` |
  | `UPCP_POSTGRES_PORT` | docs/11, .env.example, compose (db) | `UPCP_PORT_POSTGRES` |
  | `UPCP_PROMETHEUS_PORT` | docs/11, .env.example, compose | `UPCP_PORT_PROMETHEUS` |
  | `UPCP_GRAFANA_PORT` | docs/11, .env.example, compose | `UPCP_PORT_GRAFANA` |
  | `UPCP_FRONTEND_DEV_PORT` | docs/11, .env.example | `UPCP_PORT_FRONTEND_DEV` |

- Каноникал подтверждён корневым `docker-compose.yml` + `.env.example`:
  `UPCP_PORT_BACKEND/FRONTEND/GRAFANA/POSTGRES/PROMETHEUS/REDIS`.
- Структура: шаблоны в `FILES[...]` (`.env.example`@1690,
  `docker-compose.yml`@1748, `docs/11-docker-and-ports.md`@1083);
  импорт модуля безопасен (данные + `main()` под `__main__`-guard).
- Инфраструктура: pytest `testpaths=["backend/tests"]` → контракт-тест
  размещён там; репо-корень импортируем (прецедент `tests.conftest`);
  pre-commit ruff `files: ^backend/` (скрафтолдер хуком не проверяется —
  ручной `ruff check` прогнан отдельно).

## Acceptance Criteria (verified 2026-10-25)

- [x] Red-тест `backend/tests/test_bootstrap_scaffold.py` — шаблоны
      `.env.example`, `docker-compose.yml`, `docs/11` содержат каноникал и
      **ноль легаси-имён**: red `3 failed / 2 passed?` — нет: red
      **3 failed** (все три шаблона) → **green 3 passed, exit 0**
- [x] **14** вхождений переименованы (docs-таблица ×5, .env ×5,
      compose ×4 — бэкенд, db, prometheus, grafana); дефолтные порты
      и генерация не менялись
- [x] Полные гейты: pytest **1026 passed** (+3 контрактных),
      `ruff check backend` clean, **`ruff check bootstrap_upcp.py` clean**,
      `mypy backend/app` clean (114 файлов)
- [x] PROJECT_STATUS синхронизирован (2 пункта очереди зачёркнуты)
- [x] Отклонения зафиксированы

## Evidence

- Red: `3 failed, exit 1` — все три теста (env/compose/docs) падали на
  легаси-именах; импорт `bootstrap_upcp` в тесте сработал сходу
- Зелёный: **3 passed, exit 0**; grep-проверка легаси-остатков по
  скрафтолдеру = **0**
- Полн. гейты: **1026 passed** (exit 0), ruff backend/scaffolder 0,
  mypy 114 файлов чисто
- Примечание: контракт-тест сам поймал 14-й случай (мой первичный
  grep-инвентарь обрезался `head` — строка1760 compose db), который
  ушёл из первого прохода правок → тест как ловушка инвентарных ошибок
  отработал по назначению

## Deviations / notes (recorded per §7)

1. **`UPCP_FRONTEND_DEV_PORT` → `UPCP_PORT_FRONTEND_DEV`** (а не
   `UPCP_PORT_FRONTEND`): в корне `UPCP_PORT_FRONTEND`=3071 — это nginx
   статики, тогда как scaffold-переменная — vite-dev-сервер (дефолт35173).
   Слияние имён с разными смыслами/дефолтами вводило бы в заблуждение;
   суффикс `_DEV` сохраняет семантику при каноническом префиксе
   `UPCP_PORT_*` (контракт нарушен не был).
2. Дефолтные значения портов (38080/35432/39090/33000/35173) и вся
   механика генерации не менялись — только имена переменных.
3. Легаси-упоминания в исторических документах (PROJECT_STATUS/TASK-0119)
   намеренно НЕ переименованы — это записи о прошлом состоянии.
4. Скрафтолдер вне pre-commit ruff-скоупа (`files: ^backend/`) —
   проверен вручную (`ruff check bootstrap_upcp.py` = clean).
5. **CI-регрессия на MR !95 (pipeline505, job `backend:test`)** —
   `test_review_service::test_submit_verdict` ERROR: `UNIQUE constraint
   failed: project.slug ('test')` под CI-`-n auto` (xdist). Корень:
   фикстура `_db` делала `create_all` на setup (no-op на живых таблицах,
   drop только на teardown), а COMMIT-резиду чужих тестов на общем
   conftest-движке (источник — `test_analytics._setup_project`, мигрированный
   в TASK-0112 на shared engine) переживал их teardown-роллбек; +3 файла
   этой задачи перетасовали xdist-распределение и вскрыли порядок-
   зависимость (CI зелёным был до сих пор благодаря устойчивому порядку).
   Фикс: `drop_all`+`create_all` на setup `_db` (тот же паттерн, что
   conftest-харденинг TASK-0112) — **воспроизводимо проверено CI-
   идентичной командой локально** (`pytest backend/tests -q --tb=short -x
   -n auto` после установки pytest-xdist): **1026 passed, exit 0**.
   Sweep `create_all`-без-предшествующего-`drop` нашёл ряд других файлов
   с тем же teardown-drop-паттерном (латентная та же класс-чувствительность,
   нигде не проявлялась) → follow-up в очереди PROJECT_STATUS
   («hermetic setup-drop sweep»), не правилось в этом MR (не AC и объёмный чурн).

## Files

| File | Action |
|------|--------|
| `backend/tests/test_bootstrap_scaffold.py` | CREATE — контракт-тест шаблонов (3 теста) |
| `bootstrap_upcp.py` | MODIFY — 14 переименований (docs/11, .env.example, docker-compose.yml) |
