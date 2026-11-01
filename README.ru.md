# UPCP — Universal Project Control Plane

[English](README.md) | [Русский](README.ru.md)

![CI](https://github.com/DKovalchuk/upcp/actions/workflows/ci.yml/badge.svg)

**Self-hosted, local-first платформа управления инженерными проектами — с ИИ-агентами как полноправными участниками процесса.**

UPCP даёт команде (и её ИИ-агентам) единое место для планирования работы,
прохождения её через управляемый workflow, прикрепления доказательств и
подтверждения качества до релиза. Человек остаётся в контуре управления:
агенты предлагают — люди ревьюят и принимают.

## Содержание

- [Зачем UPCP](#зачем-upcp)
- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Стек](#стек)
- [Качество и тестирование](#качество-и-тестирование)
- [Разработка через агентов](#разработка-через-агентов)
- [Быстрый старт](#быстрый-старт)
- [Структура репозитория](#структура-репозитория)
- [Документация](#документация)
- [CI/CD](#cicd)
- [Лицензия](#лицензия)

## Зачем UPCP

Трекеры проектов строились под людей, которые кликают карточки. ИИ-агенты
сегодня выполняют реальную работу — но им нужны структурированные интерфейсы,
проверяемые доказательства и ревью-гейты, а не тикет со статусом «заблокировано».

UPCP спроектирован с обратной стороны:

- **Работа — конечный автомат.** Задачи проходят определённый жизненный цикл
  (`backlog → ready → claimed → in_progress → ready_for_review → done` плюс
  ветки blocked/clarification/cancel). Недопустимые переходы отклоняются API,
  а не по договорённости.
- **Клеймы — аренды.** Агенты явно забирают работу, подтверждают живость
  heartbeat'ами, а reaper автоматически снимает протухшие клеймы — без
  тихого двойного назначения.
- **Качество на доказательствах.** Чеклисты Definition of Done, критерии
  приёмки, загруженное evidence, раунды ревью с находками и жёсткий гейт,
  блокирующий завершение, пока проверки не пройдены.
- **Всё аудируется.** Каждый переход, клейм, ревью и решение гейта
  попадает в append-only аудит-трейл и питает дашборды.

## Возможности

- **Структура проектов** — проекты → компоненты → модули → фичи → задачи,
  с членствами и ролевой моделью доступа (RBAC).
- **Движок workflow задач** — полный жизненный цикл с серверной валидацией
  переходов, bulk-операциями, зависимостями, комментариями и подзадачами.
- **Workflow агентов** — регистрация агентов, scoped-токены, клеймы с
  heartbeat'ами, clarification'ы (агент может спросить человека; блокирующий
  вопрос останавливает часы) и reaper протухших клеймов.
- **Управление качеством** — Definition of Done, критерии приёмки, evidence
  с состояниями верификации, раунды ревью (люди и агенты), находки по
  severity, гейты завершения.
- **Отчётность и аналитика** — доски внимания, velocity, история здоровья,
  статистика качества, CSV-экспорт; каналы уведомлений (in-app, email,
  webhook) с SSE-пушем в UI.
- **Интерфейсы** — REST API (OpenAPI), **MCP-сервер** для ИИ-агентов, CLI и
  React SPA.
- **Наблюдаемость** — структурированные логи, трейсы OpenTelemetry, метрики
  Prometheus и комплектный стек Grafana/Loki/Tempo под Docker-профилем.
- **Интеграция с git (read-only)** — ветки и коммиты связаны с проектами для
  контекста, но никогда не мутируются.

## Архитектура

Модульный монолит на принципах DDD: FastAPI-приложение, организованное по
bounded context'ам с явными границами сервисов/схем/репозиториев и миграциями
через Alembic.

```text
                       ┌──────────────────────────────────────────┐
   Браузер ───────────▶│  React SPA (TanStack Router/Query, UI)   │
                       └────────────────┬─────────────────────────┘
                                        │ REST + SSE
   ИИ-агенты ── MCP ───┐               │
   CLI ────────────────┤               ▼
                       │      ┌─────────────────────┐     ┌─────────────┐
                       └─────▶│  FastAPI backend     │────▶│ PostgreSQL  │
                              │  ┌────────────────┐  │     └─────────────┘
                              │  │ api   mcp      │  │     ┌─────────────┐
                              │  │ projects  structure  │◀───│ Redis       │
                              │  │ delivery  quality│  │     └─────────────┘
                              │  │ gitread  reporting│ │
                              │  │ llm  audit  shared │ │     ┌─────────────┐
                              │  └────────────────┘  │────▶│ OTel → Tempo │
                              └─────────────────────┘     │ Prom → Grafana│
                                                           └─────────────┘
```

Bounded context'ы: `projects`, `structure`, `delivery`, `quality`, `gitread`,
`reporting`, `notifications`, `llm`, `audit`, `mcp`, `api`, `shared`,
`health`. Подробнее — [`docs/architecture/ddd-contexts.md`](docs/architecture/ddd-contexts.md)
и [`docs/INDEX.md`](docs/INDEX.md).

## Стек

| Слой | Выбор |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL 16, Redis 7 |
| Frontend | React 19, TypeScript, Vite, TanStack Router/Query, Tailwind, shadcn/ui, Recharts |
| Интерфейс для агентов | MCP (JSON-RPC 2.0), REST/OpenAPI, CLI |
| Наблюдаемость | OpenTelemetry, Prometheus, Grafana, Loki, Tempo |
| Инструменты качества | pytest, ruff, mypy, Playwright (e2e), ZAP + Kali (security), Locust (нагрузка), chaos-набор |
| Деплой | Docker Compose, Nginx, GitLab CI |

## Качество и тестирование

| Показатель | Значение |
|---|---|
| Backend-тесты | **1 073** тест-функции в 107 файлах |
| Frontend-тесты | 57 тестовых наборов (Vitest) |
| Дополнительные наборы | e2e (Playwright), security (ZAP baseline + Kali + authz/fuzz), chaos, нагрузка (Locust), lighthouse |
| Гейт покрытия | ≥ 80 % (`make coverage`) |
| Статические проверки | ruff, mypy (strict), tsc, eslint |
| Процессная документация | 29 спеков, 140+ файлов задач с AC и evidence |

CI выполняет `lint → test → quality → build → deploy`; quality gate —
жёсткий гейт (красный гейт блокирует деплои) и включает security/chaos/perf
наборы.

## Разработка через агентов

Этот репозиторий — также кейс по эксплуатации ИИ-кодящих агентов:

- [`AGENTS.md`](AGENTS.md) — операционное руководство для агентов: порядок
  чтения, экономия контекста, границы DDD, обязательный TDD, стоп-условия,
  Definition of Done, многофакторный анализ.
- **Spec Flow → TDD** — каждое нетривиальное изменение: спека → задача →
  падающий тест → реализация; спеки в [`specs/`](specs/), задачи с AC и
  evidence — в [`tasks/`](tasks/).
- **Роутинг моделей** — правило «достаточно дешёвая модель» для рутинных
  работ, эскалация для архитектурных/безопасностных задач.
- **Дисциплина доказательств** — задачи закрываются только с прошедшими
  тестами, CI-доказательствами и многофакторным анализом в файле задачи.
- [`PROJECT_STATUS.md`](PROJECT_STATUS.md) и [`ROADMAP_UNIFIED.md`](ROADMAP_UNIFIED.md)
  отслеживают состояние вех; [`CHANGELOG.md`](CHANGELOG.md) фиксирует релизы.

Более 600 коммитов первых месяцев разработки сделаны в этом workflow —
task-ветки, merge request'ы, quality gates и человеческое ревью на каждом
слиянии.

## Быстрый старт

```bash
git clone https://github.com/DKovalchuk/upcp.git
cd upcp

cp .env.example .env          # для локальной разработки достаточно значений по умолчанию
make install                  # venv + backend-зависимости
make test                     # backend-набор тестов

docker compose up --build     # полный стек (app, db, redis, frontend)
```

Проверка здоровья:

```bash
curl http://127.0.0.1:38080/health
```

Порты намеренно нестандартные и настраиваются через файлы `.env.*`
(dev 3072/38080, test 3071/38082, stage 3070/38081) — см.
[`docs/11-docker-and-ports.md`](docs/11-docker-and-ports.md). Для stage-стека
сначала создайте `.env.stage` из `.env.stage.example`.

## Структура репозитория

```text
backend/          FastAPI-приложение: bounded context'ы, модели, сервисы, API, MCP
frontend/         React SPA (Vite + Tailwind + shadcn/ui)
tests/            Сквозные наборы: e2e, security, chaos, performance, quality gate
specs/             Gherkin-спеки (SPEC-XXXX)
tasks/            Файлы задач с AC, evidence и заметками о закрытии (TASK-XXXX)
docs/             Архитектура, процессы, ops, PRD — индекс в docs/INDEX.md
scripts/          Инструменты dev/ops: сидинг, верификация, публичный экспорт
observability/    Конфигурация Prometheus/Grafana/Loki/Tempo
```

## Документация

Начните с [`docs/INDEX.md`](docs/INDEX.md) — карта всех документов с
указанием, когда читать. Ключевые точки входа:

- [`docs/00-vision.md`](docs/00-vision.md) — видение продукта
- [`docs/02-architecture.md`](docs/02-architecture.md) — архитектура системы
- [`docs/architecture/agent-workflow-state-machine.md`](docs/architecture/agent-workflow-state-machine.md) — семантика workflow
- [`docs/ENVIRONMENTS.md`](docs/ENVIRONMENTS.md) — локальные окружения и учётные данные

## CI/CD

Пайплайны запускаются на каждом merge request и на основных ветках: линт,
проверка типов, unit/integration-тесты, проверка зависимостей и контейнеров,
композитный quality gate, сборка контейнеров и деплой окружений. Релизные
слияния идут в `main` — именно его публикует это публичное зеркало.

## Лицензия

[MIT](LICENSE)
