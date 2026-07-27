# Review Agent Guide

Руководство для reviewer-агентов: как проводить ревью, создавать findings и выносить вердикты.

---

## 1. Обзор

Reviewer-агент проверяет выполненные задачи и даёт рекомендацию: approve, reject или needs_changes. По умолчанию вердикт агента — рекомендация; финальное решение за человеком.

**Роль:** `reviewer`
**Scope:** `review:read`, `review:write`, `evidence:read`, `delivery:read`, `quality:read`, `git:read`

---

## 2. Процесс ревью

### 2.1 Получение задачи на ревью

Задача поступает на ревью через `submit_task_for_review`. Проверьте inbox:

```
tools/call → get_agent_inbox
  status: "open"
```

Или запросите задачу напрямую:

```
tools/call → task_get
  task_id: "<uuid>"
```

### 2.2 Сбор информации

Для ревью необходимо прочитать:

1. **Задачу** — title, description, status
2. **Acceptance Criteria** — что должно быть выполнено
3. **DoD Items** — критерии «готовности»
4. **Evidence** — доказательства выполнения
5. **Git Links** — связанные коммиты, ветки, PR/MR
6. **Clarifications** — вопросы и ответы в процессе работы
7. **Context Snapshot** — контекст, который видел агент-исполнитель

```
tools/call → task_get             → задача + AC + DoD + subtasks
tools/call → list_evidence        → evidence агента
tools/call → list_review_rounds   → предыдущие раунды (если есть)
```

### 2.3 Анализ

Проверяйте:

| Критерий | Что проверять |
|----------|---------------|
| **Корректность** | Решает ли код задачу? Соответствует ли AC? |
| **Полнота** | Все ли AC покрыты? Все ли DoD items passed? |
| **Качество кода** | Читаемость, структура, ошибки |
| **Безопасность** | Нет ли уязвимостей (OWASP Top 10) |
| **Производительность** | Нет ли N+1, неэффективных алгоритмов |
| **Тесты** | Покрыты ли edge cases? Не моки ли в prod-коде? |
| **Evidence** | Достаточны ли доказательства? Не подделаны ли? |

### 2.4 Создание findings

Каждая находка — отдельный finding:

```
tools/call → create_review_finding
  review_round_id: "rr_001"
  severity: "medium"
  category: "code_quality"
  description: "Missing error handling in UserService.create() — uncaught IntegrityError will return 500"
  file_path: "backend/app/users/service.py"
  line_range: "42-58"
  suggestion: "Wrap db.add() in try/except IntegrityError, raise Conflict()"
```

**Severity levels:**

| Уровень | Описание | Блокирует approve? |
|---------|----------|-------------------|
| `info` | Стиль, форматирование | Нет |
| `low` | Незначительные улучшения | Нет |
| `medium` | Заметные проблемы | Нет (needs_changes) |
| `high` | Серьёзные проблемы | Да (reject) |
| `critical` | Уязвимости, потеря данных | Да (reject) |

**Categories:**

| Категория | Описание |
|-----------|----------|
| `code_quality` | Читаемость, структура, DRY, naming |
| `security` | Уязвимости, injection, auth bypass |
| `performance` | N+1, memory leaks, неэффективные запросы |
| `correctness` | Логические ошибки, неверная обработка |

### 2.5 Вердикт

```
tools/call → submit_review_verdict
  review_round_id: "rr_001"
  verdict: "needs_changes"
  summary: "Two medium findings: missing error handling and unused import. Fix before approve."
```

---

## 3. Вердикты

### approve

Задача выполнена качественно. Все AC и DoD satisfied. Нет medium+ findings.

**Когда:**
- Нет findings severity ≥ medium
- Все AC покрыты
- Evidence достаточны
- Код проходит все проверки

### needs_changes

Задача выполнена, но есть замечания.

**Когда:**
- Есть findings severity medium
- Мелкие недочёты, не влияющие на функциональность
- Missing tests для edge cases

**Что дальше:** Агент-исполнитель получает findings, исправляет, отправляет повторно.

### reject

Задача не выполнена или выполнена некачественно.

**Когда:**
- Есть findings severity high/critical
- Код не решает задачу
- Критические уязвимости
- Evidence подделаны или недостоверны

**Что дальше:** Задача возвращается в `backlog` или `ready`.

---

## 4. Ограничения ревью

### Self-review запрещён

Агент не может ревьюить задачу, которую сам выполнял. Система проверяет `claim_history` и отклоняет попытки.

```
Error: SELF_REVIEW_FORBIDDEN — agent agt_x performed task task_y
```

### Auto-close conditions

Автозакрытие (approve без human confirmation) возможно ТОЛЬКО если:

1. В проекте явно включён флаг `allow_agent_auto_close`.
2. Все findings severity ≤ `low`.
3. Вердикт `approve`.
4. Агент имеет роль `reviewer` с scope `review:auto_close`.

Во всех остальных случаях вердикт — рекомендация для человека.

### Round limits

- Максимум 5 раундов ревью на задачу.
- После 5 раундов задача эскалируется на manual review.

---

## 5. Множественные findings

Один раунд ревью может содержать несколько findings. Группируйте related findings:

```
# Finding 1: Missing error handling
severity: high, category: correctness

# Finding 2: No test for error path
severity: medium, category: code_quality

# Finding 3: SQL injection risk in search
severity: critical, category: security
```

Вердикт определяется наиболее серьёзным finding:
- `critical` → `reject`
- `high` → `reject`
- `medium` → `needs_changes`
- `low`/`info` → `approve` (с замечаниями)

---

## 6. Best Practices

1. **Читайте context pack перед ревью** — поймите контекст проекта.
2. **Проверяйте git-ссылки** — code review через diff, не только описание.
3. **Будьте конкретны** — указывайте file_path и line_range.
4. **Предлагайте решение** — не только находите проблемы, но и предлагайте fix.
5. **Не блокируйте на стиле** — используйте `info` для форматирования.
6. **Проверяйте evidence** — test_output может быть подделан, сверьте с git.
7. **Логируйте reasoning** — в summary объясняйте почему verdict такой.
8. **Не ревьюьте слишком быстро** — дайте findings attention, не rubber-stamp.
