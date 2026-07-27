# Project Drill-Down UX

Иерархическая навигация: Portfolio → Project → Component → Module → Feature → Task.

---

## 1. Иерархия

```
Portfolio (/projects)
└── Project (/projects/:id)
    └── Component (expand in Structure tab)
        └── Module (expand in Component)
            └── Feature (group header in Delivery tab)
                └── Task (sheet or page)
                    ├── Subtask
                    ├── AcceptanceCriterion
                    ├── DoDItem
                    ├── Evidence
                    ├── ReviewRound → ReviewFinding
                    ├── ClarificationRequest
                    └── Audit trail
```

---

## 2. Navigation Patterns

### 2.1 Breadcrumbs

Всегда видимы в BreadcrumbBar:

```
Dashboard > Projects > UPCP v2 > Delivery > TASK-0042
```

- Каждый элемент кликабелен.
- Последний — текущая страница (не ссылка).
- На мобильных: последние 3 уровня + "..." для остальных.

### 2.2 Deep Links

| Ресурс | URL | Тип |
|--------|-----|-----|
| Проект overview | `/projects/:id` | page |
| Проект + tab | `/projects/:id?tab=delivery` | page + tab |
| Компонент | `/projects/:id/structure?component=:cid` | expand |
| Модуль | `/projects/:id/structure?component=:cid&module=:mid` | expand |
| Feature | `/projects/:id/delivery?feature=:fid` | expand |
| Task (sheet) | `/projects/:id/delivery?task=:tid` | sheet |
| Task (page) | `/projects/:id/tasks/:tid` | page |

### 2.3 URL State Sync

Все UI-состояния синхронизируются с URL search params:

| Param | Тип | Описание |
|-------|-----|----------|
| `tab` | string | Активная вкладка проекта |
| `component` | UUID | Раскрытый компонент |
| `module` | UUID | Раскрытый модуль |
| `feature` | UUID | Раскрытая feature |
| `task` | UUID | Открытый task detail sheet |
| `view` | `list` \| `board` | Режим delivery |
| `page` | int | Номер страницы |
| `pageSize` | int | Размер страницы |
| `search` | string | Поисковый запрос |
| `status` | string | Фильтр статуса |
| `sort` | string | Сортировка |

**Поведение:**
- Навигация назад/вперёд восстанавливает состояние.
- Share URL открывает ту же view.
- Cmd+click открывает в новой вкладке.

---

## 3. Portfolio Level (`/projects`)

### Project Table

**Колонки:** Name, Status, Components, Tasks (total), Active Tasks, Last Activity.

**Функции:** Поиск, фильтр по статусу, сортировка, пагинация (URL-synced), клик → project detail.

---

## 4. Project Level (`/projects/:id`)

### Tabs

| Tab | Контент |
|-----|---------|
| Overview | Статус, описание, stats cards |
| Structure | Components → Modules |
| Delivery | Features → Tasks |
| Quality | AC/DoD статистика |
| Agents | Назначенные агенты |
| Evidence & Reviews | Evidence list, review rounds |
| Git | Providers, branches, commits, links |
| Audit | Timeline |
| Settings | Настройки проекта |

Tab state synced с `?tab=` URL param.

---

## 5. Component Level (Structure tab)

Card grid для компонентов. Клик → expand с таблицей модулей.

```
┌─────────────────────────────────┐
│ Backend Core                    │
│ Status: active · 5 modules      │
│ ▼                               │
├─────────────────────────────────┤
│ │ Module        │ Status │ Tasks│ │
│ │ User Module   │ active │ 8    │ │
│ │ Auth Module   │ active │ 5    │ │
└─────────────────────────────────┘
```

---

## 6. Module Level (expand inside Component)

Таблица модулей: Name, Status, Features count, Tasks count. Клик → фильтрует Delivery tab.

---

## 7. Feature Level (Delivery tab)

Features — collapsible группы задач.

```
▼ Auth System (feat_001) — 8 tasks · 3 done · 2 in progress
  ├─ [P1] Add User model              ready      claude-builder
  ├─ [P0] JWT authentication           in_progress claude-builder
  └─ [P2] Password reset flow          backlog     unassigned
```

**View toggle:** List / Board (Kanban).

---

## 8. Task Level

### Sheet (slide-over)

По умолчанию. См. [task-detail.md](./task-detail.md).

### Full Page (`/projects/:id/tasks/:tid`)

По deep link. Тот же контент в полноэкранном макете.

---

## 9. Saved Views

Пользователь сохраняет комбинацию фильтров:

```
Saved View: "My blocked tasks"
  - status: blocked
  - assignee: me
  - project: UPCP v2
```

**Хранение:** localStorage + optional server-side. **UI:** Dropdown "Saved Views" в toolbar.

---

## 10. Keyboard Navigation

| Key | Действие |
|-----|----------|
| `Cmd+K` | Command palette |
| `[` / `]` | Previous / next tab |
| `Esc` | Close sheet |
| `j` / `k` | Navigate list items |
| `Enter` | Open selected item |
| `Cmd+Click` | Open in new tab |
