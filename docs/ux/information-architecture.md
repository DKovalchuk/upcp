# Information Architecture

Структура навигации и страниц UPCP.

---

## 1. Навигационная структура

### Top Bar

```
[Logo] [Global Search (Cmd+K)] [Notifications Bell] [User Menu]
```

### Sidebar

```
MAIN
  Dashboard (/)
  Projects (/projects)
  ─────────────────────
PROJECT (contextual, when project selected)
  Overview (/projects/:id)
  Structure (/projects/:id/structure)
  Delivery (/projects/:id/delivery)
  Quality (/projects/:id/quality)
  Agents (/projects/:id/agents)
  Evidence & Reviews (/projects/:id/evidence)
  Git (/projects/:id/git)
  Audit (/projects/:id/audit)
  Settings (/projects/:id/settings)
  ─────────────────────
SYSTEM
  Agent Center (/agents)
  Reports (/reports)
  Health (/health)
  ─────────────────────
  [Collapse sidebar]
```

**Иконки (Lucide):**

| Элемент | Иконка |
|---------|--------|
| Dashboard | `LayoutDashboard` |
| Projects | `FolderKanban` |
| Overview | `Info` |
| Structure | `Boxes` |
| Delivery | `GitBranch` |
| Quality | `ShieldCheck` |
| Agents | `Bot` |
| Evidence | `FileCheck` |
| Git | `GitFork` |
| Audit | `ScrollText` |
| Settings | `Settings` |
| Agent Center | `BrainCircuit` |
| Reports | `BarChart3` |
| Health | `Activity` |
| Notifications | `Bell` |

---

## 2. Страницы

### Dashboard (`/`)

**Вид:** Attention Dashboard — фокус на том, что требует внимания.

**Секции:**
- Needs your review
- Open agent questions
- Blocked tasks
- Stale agent claims
- Failed quality gates
- Recent agent activity

См. [attention-dashboard.md](./attention-dashboard.md).

---

### Portfolio / Project List (`/projects`)

Таблица проектов с поиском, фильтром по статусу, сортировкой.

**Колонки:** Name, Status, Components, Tasks, Last Activity.

---

### Project Detail (`/projects/:projectId`)

**Макет:** Tabbed layout с URL-synced tabs.

| Tab | Route | Содержимое |
|-----|-------|-----------|
| Overview | `/projects/:id` | Статус, описание, статистика |
| Structure | `/projects/:id/structure` | Components → Modules |
| Delivery | `/projects/:id/delivery` | Features → Tasks (list/board) |
| Quality | `/projects/:id/quality` | AC/DoD статистика, quality gates |
| Agents | `/projects/:id/agents` | Назначенные агенты, claims |
| Evidence & Reviews | `/projects/:id/evidence` | Evidence list, review rounds |
| Git | `/projects/:id/git` | Providers, branches, commits, links |
| Audit | `/projects/:id/audit` | Timeline с фильтрами |
| Settings | `/projects/:id/settings` | Настройки проекта |

---

### Component Detail

Внутри Structure tab. Раскрывается accordion/card для просмотра модулей.

---

### Module Detail

Внутри Component expand. Таблица модулей с колонками: Name, Status, Features.

---

### Feature Detail

Внутри Delivery tab. Feature как группа задач с collapsible header.

---

### Task Detail

**Макет:** Sheet (slide-over) по умолчанию. Полная страница по deep link.

**Вкладки:** Details, Execution, Clarifications, Evidence, DoD, Subtasks, Reviews, Git, Audit.

См. [task-detail.md](./task-detail.md).

---

### Agent Center (`/agents`)

Управление агентами. Список + детали.

См. [agent-center.md](./agent-center.md).

---

### Notifications (`/notifications`)

История уведомлений с фильтрами.

См. [notifications.md](./notifications.md).

---

### Reports (`/reports`)

Глобальный список отчётов. Генерация daily/weekly. Экспорт markdown.

---

### Health (`/health`)

Статус: backend, DB, Redis, MCP. Auto-refresh.

---

### Settings (global)

Настройки: профиль, уведомления, тема. `/settings` route.

---

## 3. Breadcrumbs

```
Dashboard > Projects > UPCP v2 > Delivery > TASK-0042
```

Правила:
- Каждый элемент — кликабельная ссылка.
- Последний элемент — текущая страница (не ссылка).
- На мобильных — показываются последние 3 уровня.

---

## 4. Deep Links

| Ресурс | URL |
|--------|-----|
| Проект | `/projects/:id` |
| Проект + tab | `/projects/:id?tab=delivery` |
| Компонент | `/projects/:id/structure?component=:cid` |
| Задача (sheet) | `/projects/:id/delivery?task=:tid` |
| Задача (page) | `/projects/:id/tasks/:tid` |
| Агент | `/agents/:id` |
| Отчёт | `/reports/:id` |

---

## 5. URL State

Состояние UI синхронизируется с URL:

- `?tab=` — активная вкладка проекта
- `?task=` — открытый task detail sheet
- `?component=` — раскрытый компонент
- `?view=list|board` — режим отображения delivery
- `?page=&pageSize=` — пагинация
- `?search=` — поисковый запрос
- `?status=` — фильтр по статусу

---

## 6. Responsive Behavior

| Breakpoint | Sidebar | Контент |
|-----------|---------|---------|
| < 768px | Hidden, overlay | `px-4` |
| 768–1023px | Collapsed (64px, icons) | `px-6` |
| ≥ 1024px | Expanded (240px) | `px-8`, max-width 1400px |
