# Аналитическая записка: Комплексный аудит UPCP

> **Дата**: 2026-08-08
> **Версия проекта**: 0.16.0 (develop)
> **Аудитор**: AI Agent
> **Объём аудита**: кодовая база, документация, архитектура, спецификации, задачи

---

## Резюме

UPCP (Universal Project Control Plane) — это self-hosted платформа для совместной работы людей и AI-агентов над инженерными проектами. За 2 недели интенсивной разработки (24–27 июля + 7 августа) реализован значительный объём функциональности: от каркаса до работающей платформы с авторизацией, агентным воркфлоу, системой доказательств и обзоров.

**Текущее состояние**: ~70% запланированного функционала реализовано (backend + frontend). Backend M9–M11 полностью готов. Frontend: основные страницы работают, но UI для агентного воркфлоу, доказательств и обзоров не построен.

**Ключевая проблема**: расхождение между документацией и реализацией. Многие документы описывают то, что уже построено, как будто это ещё предстоит сделать.

---

## 1. Объём выполненной работы

### 1.1 Метрики кодовой базы

```
┌─────────────────────────────────────────────────────────────┐
│                    КОДОВАЯ БАЗА UPCP                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Backend (Python/FastAPI)          Frontend (React/TS)      │
│  ┌──────────────────────┐         ┌──────────────────────┐  │
│  │ 181 файл             │         │ 157 файлов           │  │
│  │ ~9,600 строк         │         │ ~15,200 строк        │  │
│  │ 62 тест-файла        │         │ 34 тест-файла        │  │
│  │ 19 миграций          │         │ 238 тестов           │  │
│  │ 12 API-роутеров      │         │ 11 API-модулей       │  │
│  │ 13 DDD-контекстов    │         │ 22 хука              │  │
│  └──────────────────────┘         └──────────────────────┘  │
│                                                             │
│  MCP Server: 20+ инструментов                               │
│  CLI: Typer-based команды                                   │
│  Документация: 48+ файлов                                   │
│  Спецификации: 18 файлов                                    │
│  Задачи: 81 файл                                            │
│                                                             │
│  ИТОГО: ~24,800 строк production-кода                       │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Архитектура (DDD-контексты)

```
┌─────────────────────────────────────────────────────────────────┐
│                     DDD BOUNDED CONTEXTS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  identity/   │ │  delivery/  │ │  quality/   │               │
│  │  13 файлов   │ │  6 файлов   │ │  3 файла    │               │
│  │  User,Org,RBAC│ │ Task,Feature│ │ Evidence,DoD│               │
│  │  JWT,Agents  │ │ Lifecycle   │ │ Review      │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  reporting/  │ │  shared/    │ │  mcp/       │               │
│  │  6 файлов    │ │  16 файлов  │ │  5 файлов   │               │
│  │  Dashboard   │ │  Config,DB  │ │  Server     │               │
│  │  Portfolio   │ │  Redis,Log  │ │  Tools      │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  structure/  │ │  gitread/   │ │  audit/     │               │
│  │  3 файла     │ │  4 файла    │ │  3 файла    │               │
│  │  Component   │ │  Local/GH   │ │  AuditEvent │               │
│  │  Module      │ │  Adapters   │ │  Append-only│               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  projects/   │ │  auth/      │ │  search/    │               │
│  │  3 файла     │ │  2 файла    │ │  1 файл     │               │
│  │  Project CRUD│ │  Auth models│ │  Global     │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐                                │
│  │  llm/        │ │  api/v1/    │                                │
│  │  2 файла     │ │  12 роутеров│                                │
│  │  Gateway     │ │  REST API   │                                │
│  │  Redaction   │ │             │                                │
│  └─────────────┘ └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Вехи (Milestones)

```
Временная шкала разработки UPCP
═══════════════════════════════════════════════════════════════

24 июля ──── 25 июля ──── 26 июля ──── 27 июля ──── 30 июля ──── 7 авг
  │             │             │             │             │           │
  M0            M2            M4            M7-M11        M12         M13-M14
  Foundation    Structure     MCP/CLI       Auth/Agent    Fixes       Cleanup
  M1            M3            M5-M6         Workflow      Security    Perf/A11y
  Projects      Git           Frontend      Evidence      CORS/SSRF   Tests
                               Reports      Review        Rate limit  Polish

  ◄─── 1 день ──►◄── 1 день ─►◄── 1 день ─►◄── 1 день ─►◄─ 3 дня ─►◄─ 1 день ►

  ВСЕГО: ~2 недели календарного времени
  ОЦЕНКА VERSIONING.md: 18 недель (9 спринтов)
  ФАКТИЧЕСКАЯ СКОРОСТЬ: ~9x быстрее оценки
```

---

## 2. Анализ функциональности

### 2.1 Что работает (полный стек)

| Функция | Backend | Frontend | Тесты | Качество |
|---------|---------|----------|-------|----------|
| CRUD проектов | ✅ | ✅ | ✅ | Высокое |
| Структура (Component/Module) | ✅ | ✅ | ✅ | Высокое |
| Доставка (Feature/Task/Subtask) | ✅ | ✅ | ✅ | Высокое |
| Качество (AC/DoD) | ✅ | ✅ | ✅ | Высокое |
| Аудит (события) | ✅ | ✅ | ✅ | Высокое |
| Git интеграция (read-only) | ✅ | ✅ | ✅ | Среднее |
| Авторизация (JWT/RBAC) | ✅ | ✅ | ✅ | Высокое |
| Агенты (модель/токены) | ✅ | ✅ | ✅ | Высокое |
| MCP сервер | ✅ | — | ✅ | Высокое |
| CLI | ✅ | — | ✅ | Среднее |
| Отчёты | ✅ | ✅ | ✅ | Среднее |
| Attention Dashboard | ✅ | ✅ | ✅ | Высокое |
| Уведомления | ✅ | ✅ | ✅ | Среднее |
| Портфолио | ✅ | ✅ | ✅ | Высокое |
| Поиск | ✅ | ✅ | ✅ | Среднее |
| Redis/Rate limiting | ✅ | — | ✅ | Высокое |
| Безопасность (CORS/SSRF/headers) | ✅ | — | ✅ | Высокое |
| Dark mode | — | ✅ | ✅ | Высокое |
| Command Palette (Cmd+K) | — | ✅ | ✅ | Высокое |
| Board/Kanban view | — | ✅ | ✅ | Высокое |
| Drag-and-drop | — | ✅ | ✅ | Среднее |
| Pagination | — | ✅ | ✅ | Высокое |

### 2.2 Backend готов, Frontend частично

| Функция | Backend | Frontend Types | Frontend UI | Что не сделано |
|---------|---------|---------------|-------------|----------------|
| Claim/Release/Heartbeat | ✅ | ✅ | TaskDetailSheet показывает данные | Нет UI управления клеймом |
| Clarification Flow | ✅ | ✅ | ClarificationBanner | Нет страницы управления |
| Evidence Attach/Verify | ✅ | ✅ | ReviewVerdictCard | Нет страницы доказательств |
| Review Rounds | ✅ | ✅ | ReviewVerdictCard | Нет UI обзоров |
| Agent Inbox/Playbook | ✅ | ✅ | AgentActivitySummary | Нет Agent Center |
| Task Dependencies | ✅ | — | — | Нет UI |
| Context Pack | ✅ | — | — | Нет UI |

### 2.3 Что НЕ реализовано

| Функция | Документация | Статус |
|---------|-------------|--------|
| OpenTelemetry трейсинг | 7 арх. документов | Только skeleton middleware |
| Grafana дашборды | ops/grafana-dashboards.md | Не реализовано |
| Agent Center UX | ux/agent-center.md | Не реализовано |
| WebSocket уведомления | PRD упоминает | Только polling |
| E2E тесты критических флоу | testing/e2e-critical-flows.md | 12 базовых Playwright тестов |
| Permission matrix тесты | testing/permission-matrix-tests.md | Не реализовано |
| MCP contract тесты | testing/mcp-contract-tests.md | Не реализовано |
| Backup/restore | ops/backup-restore.md | Не реализовано |
| Agent playbook (per-project) | PRD + agent docs | Endpoint есть, storage нет |
| Encrypted fields | security doc | Не реализовано |
| Idempotency keys | MCP tools spec | Не реализовано |
| PDF отчёты | PRD | Не реализовано |
| Agent auto-close | PRD | Не реализовано |

---

## 3. Найденные противоречия

### 3.1 Конфликт ID спецификаций

```
⚠️  SPEC-0015 используется ДВАЖДЫ:

    specs/SPEC-0015-evidence-review.md      — спецификация M10 (Evidence & Review)
    specs/SPEC-0015-m15-production-ready.md — спецификация M15 (Production Ready)

    РЕШЕНИЕ: Переименовать M15 спецификацию в SPEC-0017
```

### 3.2 Три разных определения lifecycle задачи

```
PRD (agent-workflow.md):
  open → claimed → in_progress → in_review → done

Planning Report:
  backlog → ready → claimed → in_progress → done

Реальный код (lifecycle.py):
  10 состояний: backlog, ready, claimed, in_progress,
  blocked, needs_clarification, ready_for_review,
  changes_requested, done, cancelled

  ⚠️  PRD и Planning Report НЕ соответствуют коду
  ✅  Код = единственный source of truth
```

### 3.3 Два определения состояний Evidence

```
PRD (evidence-and-review.md):
  pending | accepted | rejected

SPEC-0015 (evidence-review.md):
  unverified → agent_verified → human_accepted / rejected / stale

  ⚠️  PRD устарел, SPEC соответствует коду
```

### 3.4 M15 spec игнорирует готовый backend M9–M11

```
SPEC-0015-m15-production-ready.md описывает:
  "Implement task claim endpoint"      — УЖЕ СДЕЛАНO в M9
  "Implement heartbeat endpoint"       — УЖЕ СДЕЛАНO в M9
  "Implement evidence attachment"      — УЖЕ СДЕЛАНO в M10
  "Implement review round creation"    — УЖЕ СДЕЛАНO в M10

TASK-0098 тоже перечисляет эти как новые задачи.

  ⚠️  Спецификация и задача M15 требуют ПЕРЕРАБОТКИ
  Реальная работа M15: frontend UI + E2E тесты + observability
```

### 3.5 VERSIONING.md не обновлён

```
VERSIONING.md:    "0.16.0 — in progress"
PROJECT_STATUS.md: "M14 — COMPLETE"
CHANGELOG.md:     "[0.16.0] — in progress"

  ⚠️  Версия 0.16.0 должна быть отмечена как завершённая
  S16.1–S16.4 все помечены DONE
```

### 3.6 TODO в завершённой задаче

```
backend/app/identity/auth.py:76:
  # TODO: Implement agent token verification (TASK-0068)

TASK-0068 помечена как DONE в PROJECT_STATUS.md

  ⚠️  Agent token verification может быть неполным
```

### 3.7 Таймаут heartbeat: три разных значения

```
architecture/agent-workflow-state-machine.md:  120 секунд
docs/prd/agent-workflow.md:                    7 минут (stale), 15 минут (dead)
docs/agent/agent-playbook.md:                  30 минут (claim TTL)

  ⚠️  120 секунд — слишком агрессивно для реальной работы агентов
  ⚠️  30 минут — слишком долго, задача может "зависнуть"
  РЕШЕНИЕ: выбрать одно значение и синхронизировать все документы
```

### 3.8 JWT подпись: RS256 vs HS256

```
docs/security/auth-rbac.md:           JWT RS256 (асимметричный, RSA ключи)
docs/architecture/secrets-management: JWT_SECRET (симметричный ключ → HS256)

  ⚠️  КРИТИЧЕСКОЕ: RS256 требует управления RSA-ключами
  Реальный код использует JWT_SECRET → HS256
  Документ auth-rbac.md не соответствует реализации
```

### 3.9 Уровни серьёзности findings: 5 vs 3

```
docs/prd/evidence-and-review.md:        5 уровней (info, suggestion, minor, major, critical)
docs/architecture/review-engine.md:     3 уровня (info, warning, critical)

  ⚠️  Порог auto-close тоже различается:
  PRD: "нет findings >= major"
  Architecture: "нет critical findings"
```

### 3.10 LLM интеграция: есть vs нет

```
docs/02-architecture.md:         "llm" как core module, "LLM: optional assistant layer"
docs/architecture/system-context.md: "No outgoing connections to LLM providers"
docs/01-principles.md:           "Deterministic core; LLM only as assistant"

  ⚠️  Противоречие: UPCP либо обращается к LLM, либо нет
  Реально: llm/gateway.py существует, но может быть неактивен
```

### 3.11 Evidence модель: два разных определения

```
docs/prd/evidence-and-review.md:
  hash (SHA-256), file_path, submitted_by, status (pending/accepted/rejected)

docs/architecture/data-model.md:
  url, metadata, НЕТ hash, НЕТ status, НЕТ submitted_by

  ⚠️  Значительное расхождение в моделях данных
```

### 3.12 MCP tool names: PRD vs Architecture

```
docs/prd/agent-workflow.md:        claim_task, heartbeat, report_progress, report_completion
docs/architecture/mcp-tools.md:    claim_task, heartbeat_task, submit_task_for_review
docs/agent/agent-playbook.md:      create_review_finding, task_get (не существуют)

  ⚠️  Playbook ссылается на несуществующие инструменты
```

### 3.13 Отсутствующие сущности

```
docs/03-domain-model.md указывает:
  Spec           — НЕТ в data-model.md, НЕТ в коде
  GitRepo        — заменён на GitProvider + GitBranch
  GitPullRequest — НЕТ нигде

docs/prd/agent-workflow.md описывает:
  Agent Inbox    — НЕТ таблицы в data-model.md

docs/architecture/ddd-contexts.md упоминает:
  NotificationPreference — НЕТ в data-model.md

  ⚠️  Domain model не соответствует реальной схеме БД
```

---

## 4. Сильные стороны

### 4.1 Архитектура
- Чёткое разделение на DDD-контексты с соблюдением границ
- Каждый контекст: models → schemas → service (чистая трёхслойная архитектура)
- Shared контекст содержит инфраструктуру (DB, Redis, logging, rate limiting)

### 4.2 Безопасность
- JWT access + refresh токены
- RBAC с ролями и разрешениями
- Agent tokens с хешированием
- CORS конфигурируемый
- SSRF валидация
- Security headers (CSP, HSTS, X-Frame-Options)
- Rate limiting (sliding window)
- Error sanitization (без stack traces)

### 4.3 Качество кода
- TDD: 62 backend тест-файла, 34 frontend тест-файла
- 238 frontend тестов, ~189 backend тестов
- TypeScript: 0 ошибок
- Ruff: все проверки пройдены
- Mypy: 0 ошибок
- TODO/FIXME: всего 1 во всём backend

### 4.4 MCP интеграция
- 20+ инструментов для AI-агентов
- Read + write операции
- Workflow инструменты (claim, heartbeat, clarification)
- Context pack генератор

### 4.5 Скорость разработки
- M0–M14 за ~2 недели
- Полный стек: backend + frontend + тесты + документация
- Docker-based развёртывание
- Feature branch + MR workflow

---

## 5. Слабые стороны

### 5.1 Разрыв документация ↔ код
- 48+ документов описывают как реализованный, так и нереализованный функционал
- Нет чёткого маркера "реализовано" vs "запланировано"
- Агент, читающий документацию, получит неточную картину

### 5.2 Спецификации расходятся с кодом
- Task lifecycle: 3 разных определения
- Evidence states: 2 разных определения
- M15 spec не знает о готовом backend M9–M11

### 5.3 Frontend: UI для агентного воркфлоу не построен
- Backend полностью готов (claim, heartbeat, clarification, evidence, review)
- Types и API функции существуют
- Но нет UI-страниц для управления этими процессами
- TaskDetailSheet показывает данные, но не позволяет управлять воркфлоу

### 5.4 Observability только на бумаге
- 7 архитектурных документов описывают OTEL + Prometheus + Grafana
- Реально: только structured logging + tracing middleware skeleton
- Нет метрик, нет дашбордов, нет distributed tracing

### 5.5 E2E тесты минимальны
- 12 Playwright тестов (auth + базовая интеграция)
- Критические флоу (agent workflow) не покрыты
- Permission matrix тесты не реализованы

---

## 6. Векторы развития

### 6.1 Ближайшие (M15 — Production Ready)

```
┌─────────────────────────────────────────────────────────────┐
│                    M15: ПРИОРИТЕТЫ                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  P1: Исправить противоречия (1 день)                        │
│  ├── Переименовать SPEC-0015 → SPEC-0017                    │
│  ├── Обновить PRD под реальный lifecycle                    │
│  ├── Переписать M15 spec с учётом готового backend          │
│  ├── Исправить TODO в auth.py                               │
│  └── Обновить VERSIONING.md                                 │
│                                                             │
│  P2: Frontend UI для агентного воркфлоу (2–3 недели)        │
│  ├── Agent Workflow UI (claim/release/heartbeat)            │
│  ├── Clarification UI (request/answer/resolve)              │
│  ├── Evidence UI (attach/verify/accept/reject)              │
│  ├── Review UI (rounds/findings/verdict)                    │
│  ├── Agent Center page                                      │
│  └── Context Pack viewer                                    │
│                                                             │
│  P3: E2E тесты (1 неделя)                                   │
│  ├── Auth flow E2E                                          │
│  ├── Agent workflow E2E                                     │
│  ├── Clarification flow E2E                                 │
│  └── Quality gate E2E                                       │
│                                                             │
│  P4: Observability (1–2 недели)                             │
│  ├── OpenTelemetry instrumentation                          │
│  ├── Prometheus metrics endpoint                            │
│  ├── Базовые Grafana дашборды                               │
│  └── Structured logging enhancement                         │
│                                                             │
│  P5: Production hardening (1 неделя)                        │
│  ├── Graceful shutdown                                      │
│  ├── Health check improvements                              │
│  ├── Docker production config                               │
│  └── Backup/restore procedures                              │
│                                                             │
│  ОЦЕНКА: 6–8 недель до production-ready                     │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Среднесрочные (Post-1.0)

```
┌─────────────────────────────────────────────────────────────┐
│                 POST-1.0: РАЗВИТИЕ                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Multi-user & Multi-org                                     │
│  ├── Public registration                                    │
│  ├── Organization management UI                             │
│  ├── Project member management                              │
│  └── SSO/OIDC (Keycloak/Auth0)                              │
│                                                             │
│  Real-time                                                  │
│  ├── WebSocket уведомления                                  │
│  ├── Live agent activity feed                               │
│  └── Collaborative task editing                             │
│                                                             │
│  CI/CD Integration                                          │
│  ├── Webhook ingestion (GitHub/GitLab)                      │
│  ├── Auto-evidence from CI pipelines                        │
│  ├── Git write operations (PR creation)                     │
│  └── Status checks integration                              │
│                                                             │
│  Advanced Agent Features                                    │
│  ├── Agent auto-close (configurable)                        │
│  ├── Agent-to-agent collaboration                           │
│  ├── Agent performance metrics                              │
│  ├── Playbook templates                                     │
│  └── Agent skill registry                                   │
│                                                             │
│  Analytics & Reporting                                      │
│  ├── PDF отчёты                                             │
│  ├── Velocity charts                                        │
│  ├── Agent utilization dashboards                           │
│  ├── Quality trend analysis                                 │
│  └── Custom report builder                                  │
│                                                             │
│  Enterprise Features                                        │
│  ├── SAML/OIDC SSO                                          │
│  ├── LDAP integration                                       │
│  ├── Audit log retention policies                           │
│  ├── Encrypted fields in DB                                 │
│  ├── Multi-node deployment                                  │
│  └── API rate limiting per org                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Долгосрочные (Strategic)

```
┌─────────────────────────────────────────────────────────────┐
│                 STRATEGIC: ВИЗИЯ                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. SaaS Version                                            │
│     Multi-tenant, billing, hosted option                    │
│                                                             │
│  2. Plugin System                                           │
│     Custom integrations, third-party plugins                │
│                                                             │
│  3. AI-Native Features                                      │
│     Auto-task decomposition, smart assignment               │
│     Predictive analytics, risk detection                    │
│                                                             │
│  4. Mobile App                                              │
│     React Native for on-the-go monitoring                  │
│                                                             │
│  5. Marketplace                                             │
│     Playbook templates, agent configurations                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Рекомендации

### 7.1 Немедленные (сегодня)

1. **Переименовать SPEC-0015-m15-production-ready.md → SPEC-0017**
2. **Исправить TODO в identity/auth.py** (проверить, действительно ли agent token verification работает)
3. **Обновить VERSIONING.md** — отметить 0.16.0 как complete
4. **Обновить CHANGELOG.md** — добавить дату к 0.16.0

### 7.2 На этой неделе

1. **Переписать TASK-0098 и SPEC-0017** — отразить реальную работу (frontend UI, не backend)
2. **Обновить PRD** — привести task lifecycle и evidence states в соответствие с кодом
3. **Добавить маркеры в документацию** — "implemented" / "planned" / "aspirational"

### 7.3 На M15

1. **Фокус на frontend UI** — это главный пробел
2. **E2E тесты** — критические флоу должны быть покрыты
3. **Observability** — хотя бы базовые метрики
4. **Graceful shutdown** — важно для production

### 7.4 По процессу

1. **Единый source of truth** — код + PROJECT_STATUS.md, не PRD
2. **Меньше документов, больше кода** — 48+ docs для 25K строк это перебор
3. **Маркировать документы** — implemented/planned/aspirational
4. **Regular doc sync** — обновлять документацию при каждом milestone

---

## 8. Итоги

### Что получилось хорошо
- Быстрая итерация от каркаса до работающей платформы
- Чёткая архитектура с DDD-границами
- Хорошее покрытие тестами
- MCP интеграция для AI-агентов
- Реальная безопасность (не placeholder)

### Что нужно исправить
- Противоречия в документации
- Frontend UI для агентного воркфлоу
- Observability реализация
- E2E тесты
- Синхронизация документации с кодом

### Общая оценка

```
┌─────────────────────────────────────────────────────────────┐
│                    ОБЩАЯ ОЦЕНКА                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Архитектура:        ████████░░  8/10                       │
│  Качество кода:      ████████░░  8/10                       │
│  Тесты:              ███████░░░  7/10                       │
│  Документация:       █████░░░░░  5/10  (много, но расходится)│
│  Безопасность:       ████████░░  8/10                       │
│  Frontend:           ██████░░░░  6/10  (нет agent workflow UI)│
│  Backend:            █████████░  9/10                       │
│  Observability:      ██░░░░░░░░  2/10  (только skeleton)    │
│  Production readiness: █████░░░░  5/10                      │
│                                                             │
│  ИТОГО:              ██████░░░░  6.3/10                     │
│                                                             │
│  Потенциал:          █████████░  9/10                       │
│  (при завершении M15 и исправлении противоречий)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Приложение A: Структура файлов

### Backend (`backend/app/`)
```
api/v1/          — 12 роутеров (REST API)
audit/           — models, schemas, service
auth/            — models, service
delivery/        — models, schemas, service, lifecycle, workflow, dependencies
gitread/         — adapters, models, schemas, service
identity/        — 13 файлов (auth, rbac, agents, middleware)
llm/             — gateway, redaction
mcp/             — server, tools, context_pack, schemas, resources
projects/        — models, schemas, service
quality/         — models, schemas, service
reporting/       — attention, dashboard, portfolio, models, schemas, service
search/          — service
shared/          — 16 файлов (config, db, redis, logging, etc.)
structure/       — models, schemas, service
```

### Frontend (`frontend/src/`)
```
components/auth/       — LoginPage, SetupPage
components/dashboard/  — AgentActivitySummary, AttentionCards, LiveActivityFeed
components/forms/      — EntityFormDialog, entity-fields
components/layouts/    — AppShell, AppSidebar, BreadcrumbBar, TopBar
components/notifications/ — NotificationBell
components/project/    — 16 файлов (все страницы проекта)
components/ui/         — 25+ UI компонентов (shadcn + custom)
contexts/              — AuthContext
hooks/                 — 22 хука
lib/api/               — 11 API модулей
lib/                   — auth, constants, format, storage, toast, utils
test/                  — helpers, setup, test-utils
types/                 — 11 файлов типов
```

### Migrations (`backend/alembic/versions/`)
```
0002 — audit_event
0003 — project
0004 — rbac
0005 — structure
0006 — delivery
0007 — quality
0008 — fk_indexes
0009 — gitread
0010 — report
0011 — slug_unique
0012 — claim_heartbeat
0013 — clarification
0014 — task_dependencies
0015 — evidence_review
0016 — notifications
0017 — agent_tables
+ 2 initial migrations
```

---

## Приложение B: Соответствие PRD

| PRD Capability | Backend Status | Frontend Status | Gap |
|----------------|---------------|-----------------|-----|
| Identity (§3.1) | ✅ Complete | ✅ Complete | — |
| Agent Workflow (§3.2) | ✅ Complete | ⚠️ Types only | UI needed |
| Evidence (§3.3) | ✅ Complete | ⚠️ Types only | UI needed |
| Review (§3.4) | ✅ Complete | ⚠️ Types only | UI needed |
| Observability (§3.5) | ⚠️ Skeleton | — | Full impl needed |
| Human Control UX (§3.6) | ✅ Complete | ✅ Mostly done | Agent Center needed |

---

## Приложение C: Метрики покрытия тестами

| Layer | Test Files | Coverage | Notes |
|-------|-----------|----------|-------|
| Backend unit | 62 files | ~90% | Per PROJECT_STATUS |
| Backend integration | Included above | — | Real DB in tests |
| Frontend unit | 34 files | 238 tests | Vitest + RTL |
| E2E | 12 tests | Minimal | Playwright, auth + basic |
| MCP contract | — | Not tested | Documented but not implemented |
| Permission matrix | — | Not tested | Documented but not implemented |

---

*Документ создан: 2026-08-08*
*Агент-ориентированная версия: docs/AUDIT_FOR_AGENTS.md*
