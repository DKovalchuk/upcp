# UPCP v2 — Product Requirements Document

> Версия: 2.0 | Статус: Draft | Обновлено: 2026-07-27

## 1. Видение продукта

UPCP (Universal Project Control Plane) — самодостаточная, local-first платформа для совместной работы людей и AI-агентов. Платформа обеспечивает полный контроль над процессом разработки: от постановки задач до приёмки с доказательствами.

**Ключевой принцип:** каждый результат — проверяем, каждый агент — подотчётен, каждый человек — контролирует.

## 2. Целевая аудитория

| Сегмент | Описание |
|---------|----------|
| Tech Lead | Управление командой разработки, контроль качества, распределение задач |
| Solo Developer + AI | Единственный разработчик, использующий нескольких AI-агентов параллельно |
| DevOps Engineer | Наблюдаемость, развёртывание, мониторинг здоровья системы |
| AI Agent | Автономный исполнитель задач через MCP/CLI/REST интерфейсы |

## 3. Ключевые возможности

### 3.1 Identity (Идентификация)

- Организации → Проекты → Задачи (иерархия)
- Роли: `owner`, `admin`, `member`, `viewer`, `agent`
- API-ключи для агентов (scoped, rotatable)
- JWT для пользователей (access + refresh)
- RBAC матрица с проверкой на каждом эндпоинте

### 3.2 Agent Workflow (Рабочий процесс агентов)

- Жизненный цикл задачи: `open → claimed → in_progress → in_review → done`
- Heartbeat каждые 30-60 секунд, stale detection через 7 минут
- Agent inbox: входящие сообщения от людей и агентов
- Clarification flow: агент запрашивает уточнения, задача в статусе `blocked`
- Playbook: инструкции по работе для каждого проекта

### 3.3 Evidence (Доказательства)

- Типы: `test_result`, `log`, `screenshot`, `diff`, `metric`, `custom`
- Каждое доказательство привязано к задаче и шагу DoD
- DoD (Definition of Done): набор требований, которые должны быть выполнены
- Evidence completeness: % выполненных требований DoD

### 3.4 Review (Рецензирование)

- Автоматические quality gates (линтеры, тесты, типы)
- Рецензент-агент или человек
- Review rounds: несколько итераций до approval
- Findings: конкретные замечания с привязкой к файлам/строкам
- Auto-close: задача закрывается автоматически при полном approval

### 3.5 Observability (Наблюдаемость)

- OpenTelemetry: traces, metrics, logs
- Prometheus + Grafana: дашборды и алерты
- Audit log: все действия записываются с timestamp, actor, target
- Attention dashboard: что требует внимания прямо сейчас

### 3.6 Human Control UX (Управление для людей)

- Portfolio overview: все проекты на одном экране
- Project drill-down: задачи, агенты, здоровье
- Agent center: активные агенты, их текущие задачи, метрики
- Notifications: real-time через WebSocket
- Command palette (Ctrl+K): быстрый доступ к действиям

## 4. Метрики успеха

| Метрика | Цель | Измерение |
|---------|------|-----------|
| Time to first task | < 5 мин от запуска | от `docker compose up` до первой созданной задачи |
| Agent task cycle time | < 30 мин (типичная задача) | от claim до done |
| Evidence completeness | > 90% задач с полным evidence | % задач с заполненным DoD |
| Review turnaround | < 15 мин (авто) / < 2ч (human) | время от in_review до done |
| System uptime | 99.5% для self-hosted | health check成功率 |
| Stale task rate | < 5% задач | % задач без heartbeat > 7 мин |

## 5. Milestones

### M7 — Foundation (текущий)
- Docker Compose конфигурация
- Database schema (Alembic миграции)
- Auth: регистрация, вход, JWT, API-ключи
- Health check эндпоинт

### M8 — Identity & Projects
- CRUD для организаций, проектов
- RBAC матрица
- Участники проекта с ролями
- Audit log (append-only)

### M9 — Agent Workflow
- Задачи: создание, назначение, жизненный цикл
- Agent claim/release/heartbeat
- Stale detection + auto-release
- Agent inbox + clarification
- Playbook per project

### M10 — Evidence & Review
- Evidence: upload, привязка к задачам
- DoD templates
- Quality gates (lint, test, type check)
- Review workflow: round-based review
- Findings + resolution

### M11 — Observability & UX
- Attention dashboard
- Portfolio insights
- Agent center
- Notifications (WebSocket)
- Grafana dashboards
- Command palette

## 6. Scope и Non-Goals

### In Scope (v2)
- Self-hosted развёртывание через Docker Compose
- Local-first: работает без интернета
- Python/FastAPI backend, React frontend
- PostgreSQL + Redis
- MCP сервер для интеграции с AI-агентами
- REST API для всех операций
- CLI базовые команды

### Out of Scope (v2)
- Cloud/SaaS версия
- Multi-tenant изоляция на уровне БД
- Real-time collaborative editing
- Встроенный LLM (только интеграция через API)
- Мобильное приложение
- Визуальный конструктор workflow
- Выставление счетов / billing
- SSO / SAML / OIDC

## 7. Технические ограничения

- Python 3.12+, FastAPI, SQLAlchemy 2
- PostgreSQL 16, Redis 7
- React 19, Vite, Tailwind CSS
- Docker Compose (single-node)
- Семантическое версионирование (SemVer)
- OpenAPI 3.1 для всех эндпоинтов

## 8. Ссылки

- [Agent Workflow Spec](./agent-workflow.md)
- [Evidence & Review Spec](./evidence-and-review.md)
- [Human Control UX Spec](./human-control-ux.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [PROJECT_STATUS.md](../../PROJECT_STATUS.md)
