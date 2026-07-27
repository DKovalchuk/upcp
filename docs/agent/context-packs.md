# Context Packs

Документация по системе контекст-пакетов UPCP для ИИ-агентов.

---

## 1. Обзор

Context pack — это структурированный markdown-документ, содержащий релевантную информацию о проекте для агента. Генерируется на лету из БД и предоставляется через MCP resource или tool.

**Цель:** Минимизировать токены, предоставив агенту достаточно контекста для начала работы.

---

## 2. Tiers (уровни детализации)

### minimal

Минимальный контекст для проверки доступности проекта.

**Содержимое:**
- Имя проекта, slug, статус
- Количество задач по статусам

**Оценка токенов:** ~200

**Когда использовать:** Проверка connectivity, первичный обзор доступных проектов.

```
tools/call → get_context_pack
  project_id: "proj_001"
  tier: "minimal"
```

---

### standard

Стандартный контекст для начала работы над задачей.

**Содержимое:**
- Имя проекта, slug, статус, описание
- Список задач (title, status, priority)
- Git-ссылки проекта
- Краткая статистика

**Оценка токенов:** ~1000

**Когда использовать:** Перед claim_task. Обычная рабочая сессия.

---

### deep

Глубокий контекст для сложных задач.

**Содержимое:**
- Всё из `standard`
- Acceptance Criteria по задачам
- DoD items по задачам
- Evidence (последние 5 на задачу)
- Открытые clarifications
- Компоненты и модули проекта

**Оценка токенов:** ~3000

**Когда использовать:** Задачи с complex AC. Ревью. Задачи, требующие понимания архитектуры.

---

### debug

Максимальный контекст для отладки.

**Содержимое:**
- Всё из `deep`
- Audit events (последние 20)
- Subtasks по задачам
- Git commits (последние 10)
- Git branches
- Review rounds и findings
- Полные metadata всех сущностей

**Оценка токенов:** ~5000

**Когда использовать:** Отладка проблем. Audit trail анализ. Post-mortem.

---

## 3. ContextSnapshot Model

При выполнении задачи агент может зафиксировать снимок контекста:

```json
{
  "id": "cs_001",
  "task_id": "task_001",
  "agent_id": "agt_a1b2c3d4",
  "tier": "standard",
  "version": "1.0.0",
  "content_hash": "sha256:a1b2c3...",
  "token_estimate": 1042,
  "content": "# Project: UPCP v2\n\n...",
  "created_at": "2026-07-27T12:00:00Z"
}
```

### Поля

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Уникальный ID снимка |
| `task_id` | UUID | Связанная задача |
| `agent_id` | UUID | Агент, создавший снимок |
| `tier` | enum | Уровень детализации |
| `version` | semver | Версия формата context pack |
| `content_hash` | SHA-256 | Хеш содержимого для дедупликации |
| `token_estimate` | int | Оценка токенов |
| `content` | text | Markdown-содержимое |
| `created_at` | timestamp | Время создания |

---

## 4. Версионирование

Формат context pack версионируется:

| Версия | Изменения |
|--------|-----------|
| `1.0.0` | Базовый формат: project, tasks, git links |

При изменении формата инкрементируется minor/major версия. Агенты могут проверять версию через `content_hash` и кешировать.

---

## 5. Оценка токенов

`token_estimate` — приблизительное количество токенов (1 токен ≈ 4 символа для английского, ≈ 2 символа для кода). Используется для:

- Выбора tier перед отправкой в LLM
- Мониторинга стоимости
- Предупреждения о превышении context window

---

## 6. MCP Resource

Context pack доступен как MCP resource:

```
resources/list → [
  { "uri": "context_pack://project/{project_id}", "name": "Project Context Pack" }
]

resources/read → context_pack://project/{project_id}?tier=standard
```

---

## 7. CLI

```bash
# Стандартный контекст
upcp context-pack proj_001

# С указанием tier
upcp context-pack proj_001 --tier deep

# Сохранение в файл
upcp context-pack proj_001 --tier standard --output context.md

# JSON формат
upcp context-pack proj_001 --format json
```

---

## 8. Кеширование

Context pack кешируется на 5 минут. Повторный запрос с тем же `project_id` и `tier` возвращает кешированную версию. Сброс кеша при:

- Изменении задачи (status, AC, DoD)
- Прикреплении evidence
- Изменении git-ссылок
- Изменении проекта

---

## 9. Best Practices

1. **Запрашивайте минимально достаточный tier.** Не используйте `debug` без необходимости.
2. **Кешируйте content_hash.** Если хеш не изменился, контекст актуален.
3. **Запрашивайте context pack перед claim_task**, а не после.
4. **Для review** используйте `deep` — нужны AC, DoD, evidence.
5. **Для heartbeat-сообщений** не включайте контекст — это overhead.
6. **Сохраняйте snapshot** при начале работы — полезно для post-mortem.
