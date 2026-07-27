# Human Control UX — Спецификация

> Связано: [UPCP v2 PRD](./upcp-v2.md) §3.6 | Milestone: M11

## 1. Обзор

Human Control UX — интерфейс, через который человек контролирует работу AI-агентов и проектов. Приоритет: ситуационная осведомлённость (что требует внимания сейчас?) и быстрое действие (один клик до результата).

## 2. Attention Dashboard (Главная)

### 2.1 Назначение
Стартовый экран. Отвечает на вопрос: «Что требует моего внимания прямо сейчас?»

### 2.2 Секции

| Секция | Содержание | Приоритет |
|--------|-----------|-----------|
| 🔴 Blocked | Задачи, ожидающие clarification | urgent |
| 🟡 Stale | Задачи без heartbeat > 7 мин | high |
| 🟠 In Review | Задачи на рецензировании | high |
| 🟢 Active | Агенты работают | normal |
| ⚪ Recent Done | Последние завершённые | low |

### 2.3 Карточка задачи на attention dashboard

```
┌─────────────────────────────────────────────┐
│ 🔴 BLOCKED — Task #142                      │
│ "Implement user avatar upload"               │
│ Agent: claude-agent-3  •  Blocked: 23 мин    │
│ Question: "Max file size for uploads?"        │
│ [Answer] [View Task] [Release]               │
└─────────────────────────────────────────────┘
```

### 2.4 Фильтры
- По проекту
- По агенту
- По severity
- По статусу
- По дате (сегодня / неделя / всё)

## 3. Portfolio Insights

### 3.1 Обзор всех проектов

```
┌──────────────┬──────────┬──────────┬──────────┬──────────┐
│ Project      │ Active   │ Blocked  │ Stale    │ Done/week│
├──────────────┼──────────┼──────────┼──────────┼──────────┤
│ upcp-core    │ 5 tasks  │ 1 task   │ 0        │ 12       │
│ upcp-web     │ 3 tasks  │ 0        │ 1 task   │ 8        │
│ upcp-docs    │ 1 task   │ 0        │ 0        │ 15       │
└──────────────┴──────────┴──────────┴──────────┴──────────┘
```

### 3.2 Метрики на портфолио

- Velocity: задач done за неделю (тренд)
- Agent utilization: % агентов с активными claims
- Quality score: % задач, прошедших review с первого раза
- Average cycle time: от open до done

## 4. Project Drill-Down

### 4.1 Вид: Kanban Board

Колонки по статусам задач. Карточки с:
- Название задачи
- Агент (avatar/имя)
- Evidence completeness (progress bar)
- Heartbeat status (green/yellow/red)
- Приоритет badge

### 4.2 Вид: Table View

| ID | Title | Status | Agent | Evidence | Heartbeat | Actions |
|----|-------|--------|-------|----------|-----------|---------|
| 142 | Avatar upload | blocked | claude-3 | 60% | 🟡 stale | [view] [release] |

### 4.3 Фильтры и сортировка
- Статус, агент, приоритет, дата создания
- Сортировка: priority, created, updated, heartbeat

## 5. Agent Center

### 5.1 Список агентов

| Агент | Статус | Текущая задача | Claims | Done/week | Avg cycle |
|-------|--------|---------------|--------|-----------|-----------|
| claude-agent-1 | 🟢 active | #142 | 1/3 | 8 | 22 мин |
| gpt-agent-2 | ⚫ idle | — | 0/3 | 12 | 18 мин |
| gemini-agent-3 | 🔴 stale | #156 | 1/3 | 5 | 35 мин |

### 5.2 Детали агента

- Профиль: имя, модель, capabilities
- Текущие claims с heartbeat-историей
- История выполненных задач
- Настройки: max_active_claims, heartbeat_interval
- API-ключ (manage: rotate, revoke)

### 5.3 Действия
- Release claim (force release)
- Send message в inbox
- Deactivate агента
- View audit log

## 6. Notifications

### 6.1 Каналы

| Канал | Тип | Когда |
|-------|-----|-------|
| In-app toast | Real-time (WebSocket) | Все события |
| In-app inbox | Persistent | Важные события |
| Email | Async (future) | Critical: stale, blocked > 1ч |

### 6.2 События

| Событие | Приоритет | Описание |
|---------|-----------|----------|
| `task.blocked` | high | Агент запросил clarification |
| `task.stale` | high | Нет heartbeat > 7 мин |
| `task.review_ready` | normal | Задача готова к review |
| `task.changes_requested` | normal | Рецензент запросил изменения |
| `task.done` | low | Задача завершена |
| `task.auto_released` | high | Задача автоматически release |
| `agent.activated` | low | Новый агент подключился |
| `review.approved` | low | Review approved |

### 6.3 API

```
GET  /api/v1/notifications?unread=true&limit=50
POST /api/v1/notifications/{id}/read
POST /api/v1/notifications/mark-all-read
```

## 7. Reports

### 7.1 Доступные отчёты

| Отчёт | Период | Содержание |
|-------|--------|-----------|
| Weekly Summary | неделя | tasks done, agents active, issues |
| Agent Performance | настраиваемый | cycle time, success rate, evidence quality |
| Project Health | текущий | blocked, stale, velocity, quality score |
| Review Activity | неделя | reviews completed, findings, turnaround |

### 7.2 Экспорт
- PDF (future)
- JSON API для интеграций
- CSV для таблиц

## 8. Command Palette (Ctrl+K)

### 8.1 Назначение
Быстрый доступ к любому действию без навигации.

### 8.2 Команды

| Команда | Действие |
|---------|----------|
| `> task create` | Создать задачу |
| `> task find <query>` | Найти задачу |
| `> agent list` | Список агентов |
| `> project switch` | Переключить проект |
| `> review pending` | Показать ожидающие review |
| `> blocked list` | Показать blocked задачи |
| `> stale list` | Показать stale задачи |
| `> report weekly` | Сформировать отчёт |
| `> settings` | Открыть настройки |

### 8.3 Навигация
- `↑↓` — навигация по результатам
- `Enter` — выполнить/перейти
- `Esc` — закрыть
- `Tab` — автодополнение

## 9. Breadcrumbs

Путь навигации всегда виден:

```
Projects > upcp-core > Tasks > #142 "Avatar upload"
```

Каждый элемент кликабелен. Позволяет быстро вернуться на уровень выше.

## 10. Keyboard Navigation

| Комбинация | Действие |
|-----------|----------|
| `Ctrl+K` | Command palette |
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+1-5` | Switch tabs/views |
| `j/k` | Navigate list items (vim-style) |
| `Enter` | Open selected |
| `Esc` | Close modal / go back |
| `?` | Show keyboard shortcuts |

### Accessibility
- Все элементы доступны через Tab
- ARIA labels на всех интерактивных элементах
- Focus visible indicators
- Screen reader announcements для toast notifications
- Minimum contrast ratio 4.5:1 (WCAG AA)
