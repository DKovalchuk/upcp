# Review Engine — UPCP v2

## Обзор

Review Engine управляет процессом проверки выполненных задач. Поддерживает три политики ревью, автоматическое закрытие и human override.

---

## Политики ревью

### `human_only`

Только человек проводит ревью. Агент не может ни провести ревью, ни закрыть задачу автоматически.

```
Агент выполняет задачу
  → submit_task_for_review
    → ReviewRound(pending, reviewer_type=human)
      → Owner открывает UI, проводит ревью
        → submit_review_verdict(approved/rejected)
```

**Применение:** Критические задачи, security-sensitive изменения.

### `agent_review_then_human`

Агент-ревьюер проводит первичное ревью. После него — обязательное human confirmation.

```
Агент выполняет задачу
  → submit_task_for_review
    → ReviewRound(pending, reviewer_type=agent)
      → Agent-ревьюер проверяет, ставит вердикт
        → Если approved:
          → ReviewRound(completed, verdict=approved)
            → Создаётся новый ReviewRound(pending, reviewer_type=human)
              → Owner подтверждает / отклоняет
        → Если rejected:
          → Task → changes_requested
```

**Применение:** Стандартные задачи, где первичная проверка агентом ускоряет процесс.

### `agent_auto_close_if_allowed`

Агент-ревьюер может автоматически закрыть задачу без human review (при выполнении условий).

```
Агент выполняет задачу
  → submit_task_for_review
    → ReviewRound(pending, reviewer_type=agent)
      → Agent-ревьюер проверяет
        → Если approved И задача low/medium priority:
          → Task → done (автоматически)
        → Если approved И задача high/critical priority:
          → Создаётся human review round (как в agent_review_then_human)
        → Если rejected:
          → Task → changes_requested
```

**Применение:** Рутинные задачи, low-risk изменения.

---

## Модели ReviewRound и ReviewFinding

### ReviewRound

```
ReviewRound(
    id: UUID,
    task_id: UUID FK → Task,
    round_number: INT,          # Порядковый номер (1, 2, 3...)
    policy: VARCHAR(32),        # Применённая политика
    status: VARCHAR(16),        # pending → in_progress → completed | cancelled
    verdict: VARCHAR(16),       # approved | rejected (null пока не completed)
    reviewer_type: VARCHAR(16), # human | agent
    reviewer_id: UUID,          # User ID или Agent ID
    summary: TEXT,              # Итоговое ревью
    started_at: TIMESTAMPTZ,
    completed_at: TIMESTAMPTZ,
    created_at: TIMESTAMPTZ
)
```

### ReviewFinding

```
ReviewFinding(
    id: UUID,
    review_round_id: UUID FK → ReviewRound,
    severity: VARCHAR(16),      # info | warning | critical
    category: VARCHAR(32),      # correctness | security | performance | style | missing
    description: TEXT,
    file_path: TEXT,            # Путь к файлу (опционально)
    line_number: INT,           # Номер строки (опционально)
    status: VARCHAR(16),        # open | addressed | dismissed
    created_at: TIMESTAMPTZ
)
```

### Severity Semantics

| Severity | Описание | Влияние на вердикт |
|----------|----------|-------------------|
| `info` | Предложение, не блокирует | Не влияет |
| `warning` | Рекомендация, стоит исправить | Не блокирует |
| `critical` | Блокирующая находка | Автоматически → `rejected` |

### Category Taxonomy

| Категория | Описание |
|-----------|----------|
| `correctness` | Логические ошибки, edge cases |
| `security` | Уязвимости, OWASP |
| `performance` | N+1, неэффективные алгоритмы |
| `style` | Code style, naming, formatting |
| `missing` | Отсутствующие тесты, документация, error handling |

---

## Agent Reviewer Constraints

### Ограничения

1. **Scope**: Агент-ревьюер может ревьюить только задачи в назначенных проектах
2. **Self-review запрещён**: Агент не может ревьюить собственные задачи
3. **Capabilities**: Агент должен иметь capability `review.submit`
4. **Finding format**: Agent-ревьюер ОБЯЗАН приложить findings с категориями
5. **Summary required**: Краткое текстовое резюме обязательно

### Автоматические проверки агента-ревьюера

Перед вынесением вердикта, агент-ревьюер должен проверить:

1. **Evidence**: Есть ли evidence, покрывающая acceptance criteria?
2. **Tests**: Есть ли test output? Проходят ли тесты?
3. **Code quality**: Нет ли явных anti-patterns?
4. **Security**: Нет ли очевидных уязвимостей?
5. **Completeness**: Все ли acceptance criteria выполнены?

### Finding Requirements

Agent-ревьюер обязан:

- Указать severity для каждой находки
- Указать category
- Описать находку текстом
- Указать file_path и line_number если релевантно
- Критические находки ОБЯЗАНЫ привести к `rejected`

---

## Auto-Close Conditions

### Условия для auto-close (политика `agent_auto_close_if_allowed`)

Все условия должны быть истинны одновременно:

```python
def can_auto_close(task, review_round, findings):
    return (
        task.priority in ("low", "medium")              # 1. Низкий/средний приоритет
        and review_round.reviewer_type == "agent"        # 2. Ревью от агента
        and not any(                                     # 3. Нет critical findings
            f.severity == "critical"
            for f in findings
        )
        and task.evidence.count >= 1                     # 4. Есть хотя бы одно evidence
        and task.acceptance_criteria.all_met             # 5. Все AC выполнены
    )
```

### Auto-Close Process

```
1. Agent-ревьюер вызывает submit_review_verdict(approved)
2. Система проверяет can_auto_close()
3. Если ДА:
   - ReviewRound → completed, verdict=approved
   - Task → done
   - AuditEvent: review.auto_closed
   - Notification → owner: "Task auto-approved by agent"
4. Если НЕТ (high/critical priority):
   - ReviewRound → completed, verdict=approved
   - Создаётся НОВЫЙ ReviewRound(pending, reviewer_type=human)
   - Notification → owner: "Task needs your review"
```

---

## Human Override

### Правила

1. **Owner может в любой момент**:
   - Отменить текущий review round → `cancelled`
   - Создать новый review round вручную
   - Переопределить вердикт агента (approve → reject или наоборот)
   - Пропустить ревью и сразу поставить `done` (force close)

2. **Force Close**:
   ```
   Owner вызывает force_close_task(task_id, reason)
   → Отменяет все активные review rounds
   → Task → done
   → AuditEvent: task.force_closed
   ```

3. **Override Agent Verdict**:
   ```
   Owner вызывает override_review(review_round_id, new_verdict, reason)
   → ReviewRound.verdict = new_verdict
   → AuditEvent: review.verdict_overridden
   → Если new_verdict=approved → Task → done
   → Если new_verdict=rejected → Task → changes_requested
   ```

---

## Review Round Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Review Round Lifecycle                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Task: in_progress                                          │
│    │                                                        │
│    │ submit_task_for_review(summary, evidence[])            │
│    ▼                                                        │
│  Task: ready_for_review                                     │
│  ReviewRound #1: pending                                    │
│    │                                                        │
│    │ start_review()                                         │
│    ▼                                                        │
│  ReviewRound #1: in_progress                                │
│    │                                                        │
│    │ Добавление findings...                                 │
│    │                                                        │
│    │ submit_review_verdict(approved|rejected, findings[])   │
│    ▼                                                        │
│  ReviewRound #1: completed                                  │
│    │                                                        │
│    ├── Если approved (и can_auto_close)                     │
│    │   → Task: done                                         │
│    │                                                        │
│    ├── Если approved (и !can_auto_close)                    │
│    │   → ReviewRound #2: pending (reviewer_type=human)      │
│    │                                                        │
│    └── Если rejected                                        │
│        → Task: changes_requested                            │
│          → Агент дорабатывает                               │
│            → submit_task_for_review(summary)                │
│              → ReviewRound #2: pending                      │
│                → ...                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Интеграция с Evidence

### Requirements

1. Для `submit_task_for_review` рекомендуется (но не обязательно) приложить evidence
2. Agent-ревьюер проверяет evidence как часть ревью
3. При auto-close evidence обязательна (хотя бы 1)
4. Типы evidence, поддерживаемые review engine:
   - `test_output` — вывод тестов (pytest, jest и т.д.)
   - `command_output` — вывод команд (build, lint)
   - `screenshot` — скриншот результата
   - `file_diff` — diff изменений
   - `url` — ссылка на результат (preview URL, PR)
   - `log` — лог выполнения

### Evidence Validation

```python
def validate_evidence_for_review(task, evidence_list):
    """Проверяет, что evidence достаточна для ревью."""
    issues = []

    has_test_output = any(e.evidence_type == "test_output" for e in evidence_list)
    has_command_output = any(e.evidence_type == "command_output" for e in evidence_list)

    if not has_test_output and not has_command_output:
        issues.append("No test or build output provided")

    # Проверяем что acceptance criteria покрыты
    ac_count = task.acceptance_criteria.count()
    if ac_count > 0 and len(evidence_list) == 0:
        issues.append("Task has acceptance criteria but no evidence")

    return issues
```

---

## Конфигурация

### Per-Project Settings

```json
{
    "review_policy": "agent_review_then_human",
    "allow_agent_auto_close": false,
    "require_evidence_for_review": true,
    "auto_close_max_priority": "medium",
    "review_timeout_days": 3,
    "max_review_rounds": 5
}
```

### Per-Task Override

Task может переопределить политику проекта:

```json
{
    "review_policy": "human_only"  // Переопределение на уровне задачи
}
```
