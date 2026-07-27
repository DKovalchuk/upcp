# Bounded Contexts — UPCP v2

## Обзор

UPCP организован как модульный монолит с чёткими границами bounded contexts. Каждый контекст — автономный модуль со своей доменной моделью, сервисами и портами. Контексты общаются через явные интерфейсы (сервисы, события, ACL).

---

## Карта контекстов

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway                                  │
│                   (FastAPI routes + MCP tools)                       │
└────────┬──────────┬──────────┬──────────┬──────────┬────────────────┘
         │          │          │          │          │
    ┌────▼───┐ ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌──▼──────┐
    │Identity│ │ Agent  │ │Delivery│ │Quality │ │Runtime  │
    │& Access│ │Mgmt    │ │Mgmt    │ │Evidence│ │Platform │
    └────┬───┘ └────┬───┘ └───┬────┘ └───┬────┘ └──┬──────┘
         │          │         │          │          │
    ┌────▼───┐ ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌──▼──────┐
    │Secrets │ │Agent   │ │Git     │ │Observ- │ │Report-  │
    │& Config│ │Workflow │ │Integr. │ │ability │ │ing      │
    └────────┘ └────────┘ └────────┘ └────────┘ └─────────┘
                                │
                           ┌────▼─────┐
                           │Notifica- │
                           │tions     │
                           └──────────┘
         ┌──────────────────────────────────┐
         │        Shared Kernel             │
         │  (base models, events, errors,   │
         │   pagination, idempotency)       │
         └──────────────────────────────────┘
```

---

## Описание контекстов

### 1. Identity & Access (`identity_access`)

**Назначение:** Аутентификация, авторизация, управление пользователями, ролями и организациями.

**Ключевые сущности:**
- `Organization` — мультитенантная единица
- `User` — аутентифицированный пользователь
- `Membership` — связь User ↔ Organization с ролью
- `Session` — активная сессия (JWT)
- `Role`, `Permission`, `RoleBinding` — RBAC-модель

**Публичный интерфейс:**
- `AuthService` — login, refresh, revoke
- `UserService` — CRUD пользователей
- `OrgService` — управление организациями
- `RBACService` — проверка权限

**ACL:** Нет входящих зависимостей от других контекстов.

---

### 2. Agent Management (`agent_management`)

**Назначение:** Управление ИИ-агентами, их токенами, scope и назначением на проекты.

**Ключевые сущности:**
- `Agent` — зарегистрированный агент (имя, тип, capabilities)
- `AgentToken` — аутентификационный токен (MCP)
- `AgentScope` — ограничения агента (проекты, операции)
- `AgentProjectAssignment` — привязка агента к проекту

**Публичный интерфейс:**
- `AgentService` — CRUD агентов
- `AgentTokenService` — выпуск/отзыв токенов
- `AgentScopeService` — управление scope

**ACL:** → `identity_access` (верификация владельца)

---

### 3. Agent Workflow (`agent_workflow`)

**Назначение:** State machine задач, heartbeat, claim/release, clarification flow.

**Ключевые сущности:**
- `TaskClaim` — активный claim на задачу
- `Heartbeat` — периодический сигнал жизни
- `ClarificationRequest` — запрос уточнения от агента
- `Subtask` — подзадача в рамках Task

**Публичный интерфейс:**
- `TaskStateMachineService` — переходы состояний
- `ClaimService` — claim/release с атомарностью
- `HeartbeatService` — запись и проверка heartbeat
- `ClarificationService` — управление clarification flow

**ACL:** → `delivery_management` (Task), → `agent_management` (Agent)

---

### 4. Delivery Management (`delivery_management`)

**Назначение:** Управление проектами, компонентами, модулями, фичами и задачами.

**Ключевые сущности:**
- `Project` — корневая единица работы
- `Component` — структурная единица проекта
- `Module` — модуль внутри компонента
- `Feature` — фича/задача бизнес-уровня
- `Task` — конкретная единица работы для агента
- `AcceptanceCriterion` — критерий приёмки
- `DoDItem` — Definition of Done элемент

**Публичный интерфейс:**
- `ProjectService` — CRUD проектов
- `ComponentService`, `ModuleService`, `FeatureService` — CRUD иерархии
- `TaskService` — CRUD задач, управление жизненным циклом

**ACL:** → `identity_access` (проверка membership)

---

### 5. Quality & Evidence (`quality_evidence`)

**Назначение:** Управление evidence, review rounds, review findings, DoD verification.

**Ключевые сущности:**
- `Evidence` — артефакт доказательства (тип, URL, содержимое)
- `ReviewRound` — раунд ревью
- `ReviewFinding` — находка в ревью (severity, status)
- `ContextSnapshot` — снимок контекста агента в момент выполнения

**Публичный интерфейс:**
- `EvidenceService` — CRUD evidence
- `ReviewService` — управление раундами ревью
- `ReviewPolicyService` — применение политик ревью

**ACL:** → `delivery_management` (Task, Feature), → `agent_management` (Agent)

---

### 6. Runtime Platform (`runtime_platform`)

**Назначение:** Инфраструктурные сервисы — БД, кэш, очереди, rate limiting, health checks.

**Ключевые компоненты:**
- Database connection pool (asyncpg)
- Redis pool (redis-py async)
- Rate limiter (sliding window)
- Health check aggregation
- Background task scheduler

**Публичный интерфейс:**
- `HealthService` — readiness/liveness
- `RateLimiter` — проверка лимитов
- `CacheService` — операции с кэшем

**ACL:** Нет доменных зависимостей.

---

### 7. Observability (`observability`)

**Назначение:** Сбор метрик, трассировок, логов, аудит-событий.

**Ключевые сущности:**
- `AuditEvent` — запись аудита (actor, action, entity, timestamp)

**Ключевые компоненты:**
- OpenTelemetry SDK интеграция
- Structured logging (structlog)
- Audit trail writer
- Prometheus metrics registry

**Публичный интерфейс:**
- `AuditService` — запись аудит-событий
- `MetricsService` — кастомные метрики

**ACL:** → все контексты (аудит)

---

### 8. Secrets & Config (`secrets_config`)

**Назначение:** Управление секретами, конфигурацией, зашифрованными полями.

**Ключевые компоненты:**
- `SecretProvider` — абстракция для чтения секретов
- `ConfigProvider` — управление конфигурацией
- `EncryptionService` — шифрование/дешифрование полей

**Публичный интерфейс:**
- `SecretService` — получение секретов
- `ConfigService` — CRUD конфигурации

**ACL:** Нет доменных зависимостей.

---

### 9. MCP, API & CLI (`mcp_api_cli`)

**Назначение:** Транспортный слой — MCP tools, REST endpoints, CLI commands. Оркестрация вызовов к доменным сервисам.

**Ключевые компоненты:**
- MCP tool handlers (read/write/admin)
- FastAPI route handlers
- CLI command handlers
- Request/response serialization
- Idempotency middleware

**Публичный интерфейс:**
- MCP tools (см. `mcp-tools.md`)
- REST endpoints (см. `api-design.md`)

**ACL:** → все доменные контексты (транспортный слой)

---

### 10. Frontend UI (`frontend_ui`)

**Назначение:** React 19 SPA — дашборды, управление проектами, ревью, агентами.

**Ключевые компоненты:**
- React 19 + TypeScript
- TanStack Router + Query
- Tailwind CSS + shadcn/ui
- WebSocket для real-time обновлений

**ACL:** → REST API (http client)

---

### 11. Reporting & Insights (`reporting_insights`)

**Назначение:** Генерация отчётов, аналитика, экспорт данных.

**Ключевые сущности:**
- `Report` — сгенерированный отчёт (тип, период, формат)

**Публичный интерфейс:**
- `ReportService` — генерация отчётов
- `AnalyticsService` — агрегация данных

**ACL:** → `delivery_management`, `quality_evidence`, `agent_workflow`

---

### 12. Git Integration (`git_integration`)

**Назначение:** Read-only интеграция с Git-провайдерами. Синхронизация коммитов, веток, MR/PR.

**Ключевые сущности:**
- `GitProvider` — подключённый провайдер (GitLab, GitHub)
- `GitBranch` — отслеживаемая ветка
- `GitCommit` — синхронизированный коммит
- `GitLink` — связь коммита с задачей/фичей

**Публичный интерфейс:**
- `GitSyncService` — синхронизация с провайдером
- `WebhookService` — обработка webhook-ов
- `GitLinkService` — управление связями

**ACL:** Нет внутренних зависимостей (внешний API)

---

### 13. Notifications (`notifications`)

**Назначение:** Уведомления для пользователей и агентов.

**Ключевые сущности:**
- `Notification` — уведомление (тип, recipient, channel, status)

**Публичный интерфейс:**
- `NotificationService` — создание и доставка уведомлений
- `NotificationPreferenceService` — настройки доставки

**ACL:** → `identity_access` (получатели), ← все контексты (источники событий)

---

## Shared Kernel

Общие компоненты, используемые всеми контекстами:

- `BaseModel` — базовая ORM-модель (id, created_at, updated_at)
- `PaginationParams`, `PaginatedResponse` — пагинация
- `DomainEvent` — базовый класс доменных событий
- `DomainError`, `NotFoundError`, `ConflictError` — ошибки
- `IdempotencyKey` — идемпотентность
- `UUID` — генерация и валидация UUID

---

## Правила взаимодействия

1. Контексты НЕ делают прямые SQL-запросы к таблицам друг друга
2. Общение через публичные сервисы или доменные события
3. ACL (Anti-Corruption Layer) транслирует модели одного контекста в DTO другого
4. Shared Kernel содержит только примитивы, не бизнес-логику
5. Изменение публичного интерфейса контекста требует обновления всех потребителей
