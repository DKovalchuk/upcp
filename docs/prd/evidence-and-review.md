# Evidence & Review — Спецификация

> Связано: [UPCP v2 PRD](./upcp-v2.md) §3.3-3.4 | Milestone: M10

## 1. Обзор

Evidence & Review обеспечивает проверяемость результатов. Каждая задача, прежде чем считаться выполненной, должна пройти quality gates и рецензирование.

## 2. Evidence (Доказательства)

### 2.1 Типы

| Тип | MIME | Описание |
|-----|------|----------|
| `test_result` | `application/json`, `text/plain` | Вывод тестов (JUnit XML, pytest output) |
| `log` | `text/plain` | Лог выполнения (build, deploy, migration) |
| `screenshot` | `image/png`, `image/jpeg` | Скриншот результата |
| `diff` | `text/plain` | Git diff изменений |
| `metric` | `application/json` | Метрики (coverage %, latency, bundle size) |
| `custom` | `*/*` | Произвольное доказательство |

### 2.2 Модель данных

```python
class Evidence:
    id: str                    # UUID
    task_id: str               # FK → tasks
    step_id: str | None        # FK → dod_steps (nullable)
    type: EvidenceType         # enum
    title: str                 # краткое описание
    content: str | None        # inline content (до 64KB)
    file_path: str | None      # путь к файлу (для бинарных)
    hash: str                  # SHA-256 содержимого
    submitted_by: str          # agent_id или user_id
    submitted_at: datetime
    status: EvidenceStatus     # pending | accepted | rejected
```

### 2.3 Статусы evidence

| Статус | Описание |
|--------|----------|
| `pending` | Загружено, ожидает проверки |
| `accepted` | Рецензент принял |
| `rejected` | Рецензент отклонил (с причиной) |

### 2.4 API

```
POST   /api/v1/tasks/{task_id}/evidence          # загрузить
GET    /api/v1/tasks/{task_id}/evidence            # список
GET    /api/v1/evidence/{id}                       # детали
PATCH  /api/v1/evidence/{id}/accept                # принять
PATCH  /api/v1/evidence/{id}/reject                # отклонить
DELETE /api/v1/evidence/{id}                       # удалить (admin+)
```

## 3. Definition of Done (DoD)

### 3.1 Шаблон DoD

Проект определяет шаблон DoD — набор шагов, которые должны быть выполнены для каждой задачи.

```python
class DodTemplate:
    id: str
    project_id: str
    name: str
    steps: list[DodStep]

class DodStep:
    id: str
    order: int
    title: str                     # "Run unit tests"
    description: str               # "All tests pass with >80% coverage"
    evidence_type: EvidenceType    # тип ожидаемого доказательства
    required: bool                 # обязательно для completion
    auto_check: str | None         # команда для автопроверки
```

### 3.2 Пример DoD

```yaml
name: "Standard DoD"
steps:
  - title: "Unit tests pass"
    evidence_type: test_result
    required: true
    auto_check: "pytest --tb=short"
  - title: "Code coverage ≥ 80%"
    evidence_type: metric
    required: true
  - title: "Lint clean"
    evidence_type: log
    required: true
    auto_check: "ruff check ."
  - title: "Type check passes"
    evidence_type: log
    required: false
    auto_check: "mypy src/"
```

### 3.3 Evidence Completeness

```
completeness = required_steps_with_accepted_evidence / total_required_steps * 100
```

- Задача может быть отправлена на review при completeness ≥ 100% для required шагов
- Опциональные шаги не блокируют review, но влияют на score

## 4. Quality Gates

### 4.1 Автоматические gates

Quality gates запускаются автоматически при `submit-review`:

| Gate | Команда | Blocker |
|------|---------|---------|
| `lint` | `ruff check .` | да |
| `test` | `pytest` | да |
| `typecheck` | `mypy src/` | нет |
| `build` | `docker build .` | нет |

### 4.2 Поведение

1. Агент вызывает `POST /tasks/{id}/submit-review`
2. Система запускает quality gates из playbook
3. Если blocker gate fail → задача возвращается в `in_progress` с `changes_requested`
4. Если все gates pass → задача переходит в `in_review`
5. Gate результаты сохраняются как evidence

### 4.3 Кастомные gates

```yaml
quality_gates:
  - name: bundle_size
    command: "npm run build && du -sh dist/"
    threshold: "500K"
    blocker: false
```

## 5. Review (Рецензирование)

### 5.1 Review Rounds

```python
class ReviewRound:
    id: str
    task_id: str
    round_number: int         # 1, 2, 3...
    reviewer_type: Literal["agent", "human"]
    reviewer_id: str
    status: Literal["in_progress", "approved", "changes_requested"]
    started_at: datetime
    completed_at: datetime | None
    summary: str | None
```

### 5.2 Workflow

1. Задача в `in_review` → система назначает рецензента
2. Рецензент проверяет evidence, код, результат
3. Рецензент создаёт findings (замечания)
4. Рецензент решает: `approve` или `request_changes`
5. При `request_changes` → агент работает над findings → новый round
6. При `approve` → задача → `done`

### 5.3 Findings

```python
class Finding:
    id: str
    review_round_id: str
    severity: Literal["info", "suggestion", "minor", "major", "critical"]
    file_path: str | None     # привязка к файлу
    line: int | None          # привязка к строке
    description: str
    status: Literal["open", "addressed", "dismissed"]
    resolution: str | None
```

### 5.4 API

```
POST /api/v1/tasks/{task_id}/submit-review
POST /api/v1/tasks/{task_id}/review/{round_id}/approve
POST /api/v1/tasks/{task_id}/review/{round_id}/request-changes
POST /api/v1/tasks/{task_id}/review/{round_id}/findings
PATCH /api/v1/review/findings/{finding_id}/resolve
GET  /api/v1/tasks/{task_id}/reviews
```

## 6. Agent Review

Агент-рецензент работает аналогично человеку:

1. Получает уведомление о новой задаче в `in_review`
2. Читает evidence, проверяет код (MCP tool: `review_task`)
3. Создаёт findings
4. Выносит verdict: `approve` или `request_changes`

### Ограничения agent review
- Агент не может review свою собственную задачу
- Agent review — advisory для критических задач (final approval — human)
- Максимум 3 rounds agent review, затем escalate to human

## 7. Human Approval

### 7.1 Требования
- Задачи с severity `critical` требуют human approval
- Задачи, затрагивающие auth/security/DB schema — требуют human approval
- Проект может настроить `require_human_review: true` для всех задач

### 7.2 Эскалация
- После 3 rounds без resolution → уведомление admin
- После 5 rounds → задача автоматически в `blocked` с эскалацией

## 8. Auto-Close Conditions

Задача автоматически переходит в `done` когда:

1. Все required DoD шаги приняты (evidence completeness = 100%)
2. Все quality gates прошли
3. Review status = `approved`
4. Нет открытых findings с severity ≥ `major`

## 9. Метрики

| Метрика | Формула |
|---------|---------|
| Review turnaround | `avg(completed_at - started_at)` по rounds |
| First-pass approval rate | `rounds[0].approved / total_tasks * 100` |
| Finding density | `total_findings / total_review_rounds` |
| Evidence completeness | `avg(completeness)` по задачам |
| Agent review accuracy | `agent_approved ∩ human_approved / agent_approved` |
