# Attention Dashboard

Главная страница UPCP. Фокус на том, что требует внимания пользователя прямо сейчас.

---

## 1. Обзор

Dashboard — не витринная статистика, а action-oriented inbox. Каждая секция содержит элементы, которые нуждаются в действии: ревью, ответ, исправление, подтверждение.

**URL:** `/`

---

## 2. Секции

### 2.1 Needs Your Review

**Что:** Задачи, отправленные агентами на ревью и ожидающие решения.

**Данные:** Task title, Agent name, Submitted at, Evidence count, Review round number.

**Действие:** Клик → task detail sheet на вкладке Reviews.

**Пустое:** "No tasks awaiting review."

---

### 2.2 Open Agent Questions

**Что:** Clarification requests от агентов, требующие ответа.

**Данные:** Task title, Agent name, Question (truncated), Blocking indicator, Created at.

**Действие:** Клик → task detail sheet на вкладке Clarifications.

**Пустое:** "No open questions from agents."

**Сортировка:** Blocking первые, затем по дате.

---

### 2.3 Blocked Tasks

**Что:** Задачи в статусе `blocked`.

**Данные:** Task title, Block reason, Blocked since, Assigned agent.

**Действие:** Клик → task detail sheet.

**Пустое:** "No blocked tasks."

---

### 2.4 Stale Agent Claims

**Что:** Claim без heartbeat > 7 минут.

**Данные:** Task title, Agent name, Last heartbeat, Claim age.

**Действие:** Клик → task detail sheet, Execution tab. Кнопка "Release claim".

**Пустое:** "All agent claims are active."

**Индикатор:** Жёлтый/оранжевый badge для stale.

---

### 2.5 Failed Quality Gates

**Что:** Задачи, где DoD items failed.

**Данные:** Task title, Failed count / Total, Specific failed items.

**Действие:** Клик → task detail sheet, DoD tab.

**Пустое:** "All quality gates passing."

---

### 2.6 Rejected Tasks

**Что:** Задачи с вердиктом `reject` в последнем review round.

**Данные:** Task title, Reviewer, Rejection summary, Rejected at.

**Действие:** Клик → task detail sheet, Reviews tab.

**Пустое:** "No rejected tasks."

---

### 2.7 Agent Verdicts Waiting Confirmation

**Что:** Агент-ревьюер вынес вердикт, human не подтвердил.

**Данные:** Task title, Reviewer agent, Verdict, Summary.

**Действие:** Клик → task detail, Reviews tab с кнопками Approve/Reject.

**Пустое:** "No verdicts awaiting confirmation."

---

### 2.8 Low Health Projects

**Что:** Проекты с низким health score.

**Метрика:**
```
health = 100
  - (blocked_tasks * 15)
  - (stale_claims * 10)
  - (failed_dod * 10)
  - (open_clarifications * 5)
  - (rejected_tasks * 10)
```

**Порог:** < 70 = low health.

**Данные:** Project name, Health score (circular progress), Top issue.

**Действие:** Клик → project detail.

**Пустое:** "All projects healthy."

---

### 2.9 Recent Agent Activity

**Что:** Последние 10 действий агентов.

**Данные:** Agent name, Action type (badge), Target (task title), Timestamp.

**Действие:** Клик → task detail или agent detail.

**Пустое:** "No recent agent activity."

---

## 3. Макет

```
+------------------------------------------------------------------+
| Dashboard                                                        |
+------------------------------------------------------------------+
| [Needs Review: 3] [Open Questions: 2] [Blocked: 1] [Stale: 0]   |
+------------------------------------------------------------------+
| Needs Your Review (3)                    | Recent Agent Activity  |
| ┌────────────────────────────────────┐   | ┌──────────────────┐  |
| │ TASK-0042  by claude-builder       │   | │ claude-builder   │  |
| │ Submitted 15m ago · 3 evidence     │   | │ claimed TASK-045 │  |
| └────────────────────────────────────┘   | └──────────────────┘  |
+------------------------------------------+------------------------+
| Open Agent Questions (2)                 | Low Health Projects    |
| ┌────────────────────────────────────┐   | ┌──────────────────┐  |
| │ 🔒 TASK-0039  "Format for dates?"  │   | │ UPCP v2  [42%]   │  |
| └────────────────────────────────────┘   | └──────────────────┘  |
+------------------------------------------+------------------------+
```

**Макет:** 2-колоночный. Левая — action items. Правая — activity + health.

**Summary cards** вверху — быстрые метрики с кликом для фильтрации.

---

## 4. Data Fetching

TanStack Query с auto-refresh каждые 30 секунд. `useDashboardAttention()` hook. staleTime 15s.

---

## 5. Empty State

Если все секции пусты:
```
All clear! No items need your attention right now.
[Go to Projects →]
```

---

## 6. Accessibility

- Каждая секция — `<section>` с `aria-label`.
- Summary cards — `role="status"` с `aria-live="polite"`.
- Кликабельные элементы — `<a>` или `<button>` с фокус-кольцом.
- Blocking indicators — `aria-label="blocking"`.
