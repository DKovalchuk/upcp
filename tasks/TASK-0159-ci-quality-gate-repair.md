# TASK-0159 — CI quality-gate repair (3 findings) [инцидент 2026-10-25]

**Source:** инцидент Дмитрия 2026-10-25: «стабильно не проходит quality gate,
разберись и исправь»; evidence — пайплайны develop #478-#512 (все красные
после #476), MR-пайплайны зелёные
**Milestone:** CI/CD reliability
**Spec:** mini-spec (AC ниже) — три независимых дефекта из логов гейтов
**Points:** 5
**Status:** DONE (2026-10-25 — все три finding закрыты: live authz 55/55, CI-команда ×2 зелёная, frontend 467)

## Investigation (2026-10-25, evidence — логи джобов GitLab)

Пайплайны develop красные стабильно с #478 (19:04); зелёные до — #476/#474.
Гейт падает по RC: `e2e_fe=1` и/или `security=1` (`e2e=0 chaos=0 perf=0`
стабильно зелёные).

### Finding 1 — authz logout-401 (security=1): детерминированный access-токен

- `tests/security/authz/test_tokens.py::test_access_token_rejected_after_logout`
  → `logout precondition -> 401: Invalid or expired token` — стабильно в
  #478/#490/#498/#500/#504/#507/#510 (в #502 случайно зелёный — граница секунды).
- Первая поломка = merge **87e31284 = TASK-0147 (logout-denylist)** — denylist
  включилась в CI (authz бежит против живого стека).
- Механизм: `TokenService.create_access_token` payload =
  `{sub, type, iat: now, exp: now+15min}` — **ни одного случайного клейма**
  (denylist.py: «payloads carry no jti»); PyJWT сериализует iat/exp в целые
  секунды → два логина одного пользователя **внутри одной секунды** дают
  идентичный raw-токен. `test_logout_revokes_refresh_token` (logout → denylist
  sha256(raw)) и целевой тест логинятся в одном окне секунды → «свежий» токен
  уже в denylist → 401. Прод-влияние тоже реальное: мгновенный re-login после
  logout в той же секунде выдаёт мёртвый токен.
- Fix: уникальный клейм (`jti` = uuid4) в access-токене → raw-токены никогда
  не повторяются; denylist (sha256 raw) менять не нужно.

### Finding 2 — e2e Agent Detail 404 (e2e_fe=1): projects/{wrong-uuid}

- `frontend/e2e/comprehensive-ui.spec.ts:425 «2.4 — Agent Detail page loads»`:
  console error «Failed to load resource … 404» +
  `FAILED REQUESTS: 404 http://localhost:5173/api/v1/projects/<uuid>`
  (в разных прогонах разные uuid — похоже на чужой id, а не на seeded project).
- Бракет: #490 (21:50) `e2e_fe=0` → **#492 (22:06) `e2e_fe=1`,
  sha e364fce = Merge TASK-0108 (M18 a11y: name-resolution useProject,
  keyboard/ARIA, nested-button)** — единственный фронтовый merge в окне.
- Ожидаемый корень: name-resolution в `useProject`/AgentDetail теперь
  резолвит проект по неверному id (нужно подтвердить чтением кода).

### Finding 3 — backend:test xdist-резиду (#508, отдельный красный)

- `test_stale_reaper.py::TestReaperTick::test_already_released_claim_not_touched`
  → `PendingRollbackError: UNIQUE constraint failed: project.slug ('test')`
  под `-n auto` ДАЖЕ после фикса fe4835d (drop+create на setup `_db`):
  1024 passed + 2 errors, `-x` оборвал. Значит, есть ещё путь создания
  project 'test' без очистки (другой фикстура/движок) — найти и закрыть.

### Также на radar

- #498: failed job `container:scan:backend` (проверить allow_failure/причину).

## Acceptance Criteria

- [x] RED→GREEN Finding 1: юнит-тест «два последовательных create_access_token
      одного пользователя дают разные raw-токены (в т.ч. в одну секунду)»;
      `jti` добавлен; `docs/security/auth-rbac.md` (задокументированное
      ограничение «no jti») синхронизирован
- [x] Live-верификация Finding 1: authz-сьют против живого стека —
      `test_access_token_rejected_after_logout` проходит (полный профиль
      baseline: authz/fuzz/zap зелёные)
- [x] RED→GREEN Finding 2: фронт-тест фиксирует корректный id на Agent
      Detail (projects/{id} получает существующий id); локальная
      доказательная верификация = root-cause + red→green; живой e2e 2.4 —
      гейтом develop после merge (среда воспроизведения)
- [x] Finding 3: residue-путь найден и закрыт классовым контракт-тестом
      (CI-команда `pytest backend/tests -q -n auto` стабильно зелёная ×2)
- [x] Gates: полный backend-сьют (1047), ruff/mypy (backend/app), frontend
      vitest/tsc/oxlint — чисто
- [x] PROJECT_STATUS: инцидент зафиксирован, статусы задач синхронизированы
- [x] Отклонения зафиксированы

## Evidence

- **Finding 1 (authz logout-401 → детерминированный JWT)**:
  - RED: `backend/tests/test_token.py::test_consecutive_access_tokens_unique_within_same_second`
    (frozen clock — monkeypatch ровно `app.identity.token_service.datetime`)
    падал на старом коде: два токена байт-в-байт идентичны
    (`AssertionError: assert first != second`); GREEN: `+import uuid`,
    `+jti: str(uuid.uuid4())` в payload. Auth-блок: 35 passed.
  - Sweep claim-ассертов (`payload ==` / `len(payload)` / `keys()`) по
    `backend/tests` + `tests/security`: только per-key membership →
    **0 правок** существующих тестов.
  - **Live `DONE_LIVE6`** (env-lifecycle, профиль baseline против живого
    стека): **authz total=55 passed=55 failed=0** (бывший 54/1 — logout-тест
    теперь зелёный), fuzz 55/55, zap 3/3 (0 fail-findings), **RUN_RC=0**,
    стек демонтирован чисто.
- **Finding 2 (e2e Agent Detail 404)**:
  - Root cause подтверждён кодом: `BreadcrumbBar` брал **первый uuid пути**
    как project-id → на `/agents/<agentId>` — `GET /api/v1/projects/<agentId>`
    → 404 (и крамб «Project» на странице агента).
  - RED regression-тест (`BreadcrumbBar.test.tsx`, 1 failed) → GREEN после
    фикса (`projectIdFrom` — только сегмент после `projects`;
    крамб — только для project-uuid) — **5/5**.
  - Frontend-гейты: **vitest 467 passed**, `tsc -b` 0, `oxlint` 0 errors.
- **Finding 3 (xdist-резиду классово)**:
  - Контракт-тест `backend/tests/test_db_fixture_contract.py` RED: **21 файл**
    с `_db`-фиксурой `create_all` без drop-first (в т.ч. падавший
    `test_stale_reaper`) → sweep-фикс (вставка `drop_all(bind=<тот же>)` перед
    первым `create_all`) → контракт **GREEN**.
  - **CI-идентичный `pytest backend/tests -q --tb=short -x -n auto` ×2:
    RC=0/0, 1047 passed** (класс падал в #508 до фикса).
- **Гейты (итог, merged tree)**: полный сьют **1047 passed**; `ruff check
  backend` + `ruff format --check` clean; `mypy backend/app` — 114 файлов
  clean; frontend vitest/tsc/oxlint чисто.
- **Radar**: `container:scan:backend` (#498/job 3745) — `allow_failure: true`,
  причина = trivy DB download (`mirror.gcr.io` network unreachable, внешняя
  сеть) → на quality gate не влияет.

## Deviations / notes

- **«Стабильно красный» гейт = два независимых дефекта**: `e2e_fe=1` (с #492,
  merge TASK-0108) и `security=1` (с #478, merge TASK-0147); плюс
  `backend:test` (#508) — та же ловушка резиду, что fe4835d чинил точечно
  только в shared-conftest. Все три воспроизведены и закрыты в рамках задачи.
- **Контракт взят классовый** (21 файл + guard-тест в стиле text-level
  контрактов проекта), а не точечно один test_stale_reaper — иначе класс
  бы продолжил сыпаться по одному файлу в спринтах.
- **False-positive первого варианта контракта** (упоминание `create_all` в
  прозе/докстрингах) устранён сравнением позиций операторов
  `Base.metadata.*_all` — список сузился с 22 до 21 настоящих нарушителей.
- **teardown-drop в файлах оставлен** (не входил в наблюдаемый класс отказов;
  канон conftest сносит только на setup) — если в логах проявится
  кросс-воркерный teardown-race, это отдельный follow-up.
- **e2e-верификация Finding 2**: локальный живой frontend-e2e не гонялся
  (тяжёлый сетап vite+стек, конфликт с live-гейтом) — доказательная локальная
  верификация = root-cause + red→green юнит-тест; финальная живая проверка —
  quality gate develop после merge (та самая среда, где дефект упал 15+ раз).

## Files

| File | Action |
|------|--------|
| `backend/app/identity/token_service.py` | MODIFY — `jti: uuid4` в access-токене |
| `backend/tests/test_token.py` | MODIFY — red→green regression (frozen clock) |
| `docs/security/auth-rbac.md` | MODIFY — claims/лимит «no jti» → jti есть |
| `frontend/src/components/layouts/BreadcrumbBar.tsx` | MODIFY — project-id только из `projects/<uuid>` |
| `frontend/src/components/layouts/BreadcrumbBar.test.tsx` | MODIFY — regression на agent-пути |
| `backend/tests/test_db_fixture_contract.py` | CREATE — классовый guard drop-before-create |
| `backend/tests/*` (21 файл) | MODIFY — +`drop_all` перед `create_all` в `_db` |
| `tasks/TASK-0159-ci-quality-gate-repair.md` | CREATE — этот файл |
