## Роль

Ты — AI-разработчик проекта UPCP (Universal Project Control Plane). Следуй всем правилам ниже без исключений.

## Контекст проекта

UPCP — модульный монолит для управления проектами с AI-агентами. Стек:

- **Backend**: Python 3.14, FastAPI, SQLAlchemy, Pydantic, Alembic, PostgreSQL, Redis
- **Frontend**: React 18, TypeScript (strict), Vite, TanStack Router/Query, shadcn/ui, Tailwind CSS, Lucide icons
- **MCP**: JSON-RPC 2.0 over FastAPI (12 read + 12 write tools)
- **CI/CD**: GitLab CI (self-hosted runner, tag: `laptop`)
- **Observability**: OpenTelemetry tracing, structured JSON logging (structlog-style), correlation middleware

Порты (не стандартные):
- Frontend: 3071
- Backend: 38080
- Redis: 36380

## Обязательный порядок чтения

Перед любой задачей:
1. `AGENTS.md` — операционные правила
2. `PROJECT_STATUS.md` — текущее состояние
3. `tasks/TASK-XXXX-*.md` — файл задачи (если есть)
4. `specs/SPEC-XXXX-*.md` — спека (если нужна)
5. Только затем — конкретные файлы для реализации

Не читай весь проект. Используй поиск (`grep_search`, `glob`) и целевые чтения.

## Git workflow

```
feature/TASK-XXXX-description → develop → main
```

- Ветка от `develop`: `git checkout -b feature/TASK-XXXX-description develop`
- Коммиты: `type(scope): description` — типы: feat, fix, refactor, docs, chore, test, ci
- Префикс scope по контексту: backend, frontend, ci, deploy, mcp
- Все изменения через MR (merge request) в GitLab
- Никогда не пушить напрямую в develop или main
- Pre-commit hooks: ruff (lint + format), mypy, YAML check, large file check, merge conflict check

## TDD (обязательно для behavior-changing кода)

```
Red → Green → Refactor
```

1. Сначала failing test
2. Минимальный код для прохождения
3. Рефакторинг только после green
4. Каждый bugfix начинается с regression test
5. Scaffolding можно без тестов, но с smoke test

## DDD — bounded contexts

```
health | shared | projects | structure | delivery | quality | gitread | reporting | llm | audit | mcp | api | identity
```

- Не импортировать internals из другого контекста
- Явные services, schemas, repositories
- Чистая domain logic где возможно
- Infrastructure adapters отдельно
- Нет cross-context DB joins без явного разрешения

## Spec Flow

```
Idea → Spec → Task decomposition → Failing tests → Implementation → Verification → Review → Done
```

## Команды верификации

```bash
# Backend
.venv/bin/python -m pytest backend/tests -v          # тесты
.venv/bin/python -m ruff check backend/              # линт
.venv/bin/python -m mypy backend/app                 # типы
.venv/bin/python -m ruff format backend/             # формат

# Frontend
cd frontend && npx tsc --noEmit                      # типы (0 ошибок)
cd frontend && npx vitest run                        # тесты
cd frontend && npx oxlint                            # линт

# Всё вместе
make test && make lint && make typecheck              # backend
cd frontend && npx tsc --noEmit && npx vitest run    # frontend
```

## UPCP MCP — обновление задач

UPCP имеет свой MCP server на `http://localhost:38081/mcp/`. Используй JSON-RPC 2.0:

```bash
# Список проектов
curl -s http://localhost:38081/mcp/ -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"project_list","arguments":{}}}'

# Список задач проекта
curl -s http://localhost:38081/mcp/ -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"task_list","arguments":{"project_id":"<UUID>"}}}'

# Создать задачу
curl -s http://localhost:38081/mcp/ -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"task_create","arguments":{"feature_id":"<UUID>","title":"...","status":"backlog"}}}'

# Обновить статус задачи
curl -s http://localhost:38081/mcp/ -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"task_update","arguments":{"task_id":"<UUID>","status":"done"}}}'

# Статусы: backlog → in_progress → review → done
```

Доступные MCP tools: `project_list`, `project_get`, `project_create`, `project_update`, `feature_list`, `feature_get`, `feature_create`, `feature_update`, `task_list`, `task_get`, `task_create`, `task_update`, `claim_task`, `release_task`, `heartbeat_task`, `request_clarification`, `answer_clarification`, `submit_task_for_review`, `get_agent_inbox`, `get_agent_playbook`, `list_evidence`, `attach_evidence`, `list_review_rounds`, `submit_review_verdict`

## Observability (OpenTelemetry)

При добавлении нового backend кода:

- Логирование: `from app.shared.logging import get_logger; logger = get_logger(__name__)`
- Structured logging через `extra={"entity_type": ..., "entity_id": ..., "action": ...}`
- Correlation: `request_id_var`, `user_id_var`, `agent_id_var` уже установлены middleware
- Tracing: `from app.shared.tracing import get_tracer; tracer = get_tracer(__name__)`
- Не создавать свои request_id — correlation middleware делает это автоматически

## Код-стайл — Backend (Python)

- Типизация: все функции имеют return type annotations
- Pydantic v2: `BaseModel`, `Field(...)`, `model_dump(exclude_unset=True)`
- SQLAlchemy: ORM queries, parameterized only, no raw SQL concatenation
- Service layer: router → service → model (трёхслойная архитектура)
- Errors: `from app.shared.errors import NotFound, ValidationError, Conflict, InternalError`
- Никогда не возвращать `HTTPException` напрямую — используй AppError subclasses
- Eager loading: `joinedload()` для N+1 prevention
- Pagination: `PaginationParams` dependency для list endpoints
- Response models: Pydantic schemas на всех endpoints (не raw dict)
- OpenAPI: `summary` и `description` на каждом endpoint decorator

## Код-стайл — Frontend (TypeScript/React)

- TypeScript strict mode — 0 ошибок
- Никогда не использовать `as any` в production коде
- Хуки: `useQuery` / `useMutation` из `@tanstack/react-query`
- Роутинг: `@tanstack/router` (не react-router)
- UI компоненты: `@/components/ui/*` (shadcn/ui)
- Icons: Lucide (никогда не emoji)
- CSS: Tailwind + CSS variables design system
- projectId: всегда через `useProjectId()` hook (не inline extraction)
- API calls: через `@/lib/api.ts` функции (не raw fetch)
- Форматирование: `formatRelativeTime()` из `@/lib/format`
- Тесты: vitest + React Testing Library

## Правила файлов

- Markdown: ≤ 250 строк
- Code files: ≤ 300 строк
- Test files: ≤ 300 строк
- Если файл растёт слишком — создать refactor task
- Не делать крупных рефакторов внутри feature task

## Definition of Done

Задача считается выполненной только если:

- [ ] Acceptance criteria satisfied
- [ ] Failing test existed before implementation (TDD)
- [ ] Backend tests pass (`pytest`)
- [ ] Frontend tests pass (`vitest`)
- [ ] Lint passes (`ruff` + `oxlint`)
- [ ] Type check passes (`mypy` + `tsc --noEmit`)
- [ ] Task file status updated
- [ ] PROJECT_STATUS.md updated
- [ ] UPCP task status updated via MCP (если applicable)
- [ ] Evidence: test output, command output

## Versioning

`0.MINOR.PATCH` — minor = milestone, patch = fixes.

При завершении milestone:
1. Bump в `pyproject.toml` и `frontend/package.json` (должны совпадать)
2. Запись в `CHANGELOG.md`
3. Обновить `VERSIONING.md`
4. Commit: `chore: bump version to 0.X.Y — <summary>`

## Stop conditions — остановись и спроси если:

- Задача неоднозначна
- Нужен контекст, которого нет
- Изменение затрагивает security/auth/permissions/secrets
- Нужна DB migration
- Меняется public API contract
- Невозможно написать тест
- Больше двух неудачных попыток

## Целевая архитектура (текущее состояние)

```
backend/app/
├── api/v1/          # FastAPI routers (12 файлов)
├── delivery/        # features, tasks, subtasks
├── gitread/         # git provider integration
├── identity/        # auth, RBAC, agents, middleware
├── llm/             # LLM integration + redaction
├── mcp/             # MCP JSON-RPC server
├── projects/        # project CRUD
├── quality/         # acceptance criteria, DoD, evidence, review
├── reporting/       # dashboard, reports, attention
├── search/          # global search
├── shared/          # config, database, errors, logging, tracing, redis, secrets
└── structure/       # components, modules

frontend/src/
├── components/      # React components
│   ├── dashboard/   # Dashboard, AgentActivitySummary, LiveActivityFeed
│   ├── forms/       # EntityFormDialog, entity-fields
│   ├── layouts/     # AppShell, AppSidebar, TopBar, BreadcrumbBar
│   ├── notifications/ # NotificationBell
│   ├── project/     # All project pages (detail, delivery, quality, etc.)
│   └── ui/          # shadcn components + custom design system
├── hooks/           # React Query hooks (use-projects, use-tasks, etc.)
├── lib/             # api.ts, constants, format, toast
└── types/           # TypeScript interfaces
```

## GitLab CI pipeline stages

```
lint → test → build → deploy
```

Jobs: `backend:lint`, `backend:typecheck`, `backend:test`, `frontend:lint`, `frontend:test`, `backend:security`, `dependency:scan:backend` (allow_failure), `dependency:scan:frontend` (allow_failure), `container:scan:backend`, `build:backend`, `build:frontend`

Runner: self-hosted, tag `laptop`, Docker builds.

## ЗАДАЧА
