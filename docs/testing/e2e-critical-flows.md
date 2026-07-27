# E2E Critical Flows — Спецификация

> Проект: UPCP | Инструмент: Playwright (frontend) + httpx (backend) | Фреймворк: pytest

## 1. Обзор

E2E тесты покрывают 3 критических flow, которые определяют основную ценность UPCP: от создания задачи до завершения, жизненный цикл агента, и контроль через attention dashboard.

## 2. Flow 1: First-Run → Task Lifecycle

**Цель:** Проверить полный цикл «нулевого пользователя» — от регистрации до завершённой задачи.

### 2.1 Предусловия
- Чистая БД (или test fixtures)
- Браузер не авторизован

### 2.2 Шаги

| # | Действие | Ожидаемый результат |
|---|---------|-------------------|
| 1 | Открыть `/` | Redirect на `/login` |
| 2 | Нажать «Register» | Форма регистрации |
| 3 | Заполнить email + password | Валидация проходит |
| 4 | Submit | Redirect на `/setup` (first-run) |
| 5 | Создать организацию | Org создана, redirect на `/projects` |
| 6 | Создать проект | Проект создан, redirect на project page |
| 7 | Создать задачу «Implement feature X» | Задача в статусе `open` |
| 8 | Создать API-ключ для агента | Ключ отображается |
| 9 | (API) Claim задачу агентом | Статус → `claimed` |
| 10 | (API) Heartbeat | Задача остаётся `claimed` |
| 11 | (API) Upload evidence | Evidence attached |
| 12 | (API) Submit review | Статус → `in_review` |
| 13 | (UI) Увидеть задачу в «In Review» | Отображается на dashboard |
| 14 | Approve review | Статус → `done` |
| 15 | Проверить на dashboard | Задача в «Recent Done» |

### 2.3 Тест

```python
# tests/e2e/test_first_run_flow.py
class TestFirstRunFlow:
    async def test_full_lifecycle(self, browser, api_client):
        # UI: Register + setup
        page = await browser.new_page()
        await page.goto("http://localhost:35173")
        await page.click("[data-testid='register-link']")
        await page.fill("[data-testid='email']", "test@example.com")
        await page.fill("[data-testid='password']", "SecureP4ss!")
        await page.click("[data-testid='submit-register']")
        await page.wait_for_url("**/setup")

        # UI: Create org + project
        await page.fill("[data-testid='org-name']", "Test Org")
        await page.click("[data-testid='create-org']")
        await page.fill("[data-testid='project-name']", "Test Project")
        await page.click("[data-testid='create-project']")
        await page.wait_for_url("**/projects/*")

        # UI: Create task
        await page.click("[data-testid='create-task']")
        await page.fill("[data-testid='task-title']", "Implement feature X")
        await page.click("[data-testid='submit-task']")
        task_id = await page.locator("[data-testid='task-id']").text_content()

        # UI: Create API key
        await page.click("[data-testid='nav-api-keys']")
        await page.click("[data-testid='create-api-key']")
        api_key = await page.locator("[data-testid='api-key-value']").text_content()

        # API: Agent lifecycle
        headers = {"Authorization": f"ApiKey {api_key}"}
        async with httpx.AsyncClient(base_url="http://localhost:38080/api/v1") as client:
            # Claim
            resp = await client.post(f"/tasks/{task_id}/claim", headers=headers)
            assert resp.status_code == 200

            # Heartbeat
            resp = await client.post(f"/tasks/{task_id}/heartbeat", headers=headers)
            assert resp.status_code == 200

            # Evidence
            resp = await client.post(f"/tasks/{task_id}/evidence", headers=headers, json={
                "type": "test_result",
                "title": "pytest output",
                "content": "42 passed"
            })
            assert resp.status_code == 201

            # Submit review
            resp = await client.post(f"/tasks/{task_id}/submit-review", headers=headers,
                                     json={"summary": "All tests pass"})
            assert resp.status_code == 200

        # UI: Verify review state
        await page.goto(f"http://localhost:35173/tasks/{task_id}")
        await expect(page.locator("[data-testid='task-status']")).to_have_text("in_review")

        # UI: Approve
        await page.click("[data-testid='approve-task']")
        await expect(page.locator("[data-testid='task-status']")).to_have_text("done")

        # UI: Verify dashboard
        await page.goto("http://localhost:35173/")
        await expect(page.locator("[data-testid='recent-done']")).to_contain_text("Implement feature X")
```

## 3. Flow 2: Agent Authentication → Clarification

**Цель:** Проверить полный lifecycle агента с clarification flow.

### 3.1 Предусловия
- Проект с задачей в статусе `open`
- API-ключ агента создан

### 3.2 Шаги

| # | Действие | Ожидаемый результат |
|---|---------|-------------------|
| 1 | (API) Claim задачу | Статус → `claimed` |
| 2 | (API) Heartbeat с progress | Progress обновлён |
| 3 | (API) Запрос clarification | Статус → `blocked` |
| 4 | (UI) Уведомление о blocked | Toast notification |
| 5 | (UI) Attention dashboard показывает blocked | Blocked секция |
| 6 | (UI) Ответить на clarification | Clarification resolved |
| 7 | (API) Получить inbox сообщение | Message с ответом |
| 8 | (API) Resume работу | Статус → `in_progress` |
| 9 | (API) Heartbeat | Stale timer сброшен |
| 10 | (API) Submit review | Статус → `in_review` |

### 3.3 Тест

```python
# tests/e2e/test_agent_clarification_flow.py
class TestAgentClarificationFlow:
    async def test_clarification_lifecycle(self, api_client, agent_key, open_task, admin_user):
        headers = {"Authorization": f"ApiKey {agent_key}"}
        admin_headers = {"Authorization": f"Bearer {create_token(admin_user)}"}

        # Claim
        resp = await api_client.post(f"/tasks/{open_task.id}/claim", headers=headers)
        assert resp.json()["status"] == "claimed"

        # Heartbeat
        resp = await api_client.post(f"/tasks/{open_task.id}/heartbeat", headers=headers,
                                      json={"message": "Analyzing requirements", "progress": 20})
        assert resp.status_code == 200

        # Request clarification
        resp = await api_client.post(f"/tasks/{open_task.id}/clarification-request", headers=headers,
                                      json={"question": "What database schema to use?", "context": "Found 3 options"})
        assert resp.status_code == 200
        clarification_id = resp.json()["clarification_id"]

        # Verify blocked
        task = (await api_client.get(f"/tasks/{open_task.id}", headers=headers)).json()
        assert task["status"] == "blocked"

        # Admin resolves
        resp = await api_client.post(
            f"/tasks/{open_task.id}/clarifications/{clarification_id}/resolve",
            headers=admin_headers,
            json={"answer": "Use PostgreSQL with JSONB for flexibility"}
        )
        assert resp.status_code == 200

        # Agent reads inbox
        resp = await api_client.get(f"/agents/me/inbox?unread=true", headers=headers)
        messages = resp.json()["messages"]
        assert any(m["subject"].startswith("Clarification resolved") for m in messages)

        # Agent resumes
        resp = await api_client.post(f"/tasks/{open_task.id}/heartbeat", headers=headers,
                                      json={"message": "Using JSONB schema", "progress": 50})
        task = (await api_client.get(f"/tasks/{open_task.id}", headers=headers)).json()
        assert task["status"] == "in_progress"

        # Submit with evidence
        await api_client.post(f"/tasks/{open_task.id}/evidence", headers=headers, json={
            "type": "diff", "title": "Schema changes", "content": "+ create table..."
        })
        resp = await api_client.post(f"/tasks/{open_task.id}/submit-review", headers=headers,
                                      json={"summary": "Implemented with JSONB"})
        assert resp.json()["status"] == "in_review"
```

## 4. Flow 3: Attention Dashboard → Drill-Down

**Цель:** Проверить, что attention dashboard корректно отображает проблемные задачи и позволяет быстро действовать.

### 4.1 Предусловия
- Проект с несколькими задачами в разных статусах
- Пользователь авторизован

### 4.2 Шаги

| # | Действие | Ожидаемый результат |
|---|---------|-------------------|
| 1 | Открыть `/` | Attention dashboard загружен |
| 2 | Проверить «Blocked» секцию | Заблокированная задача отображается |
| 3 | Проверить «Stale» секция | Stale задача отображается с heartbeat age |
| 4 | Кликнуть на blocked задачу | Detail view открывается |
| 5 | Ответить на clarification | Форма отправлена |
| 6 | Кликнуть «Release» на stale задаче | Задача release → `open` |
| 7 | Проверить, что stale задача исчезла из секции | Обновление в реальном времени |
| 8 | Кликнуть «Audit Log» | Аудит показывает действия |

### 4.3 Тест

```python
# tests/e2e/test_attention_dashboard.py
class TestAttentionDashboard:
    async def test_dashboard_interactions(self, browser, seeded_data):
        page = await browser.new_page()

        # Login
        await page.goto("http://localhost:35173/login")
        await page.fill("[data-testid='email']", "admin@example.com")
        await page.fill("[data-testid='password']", "password")
        await page.click("[data-testid='submit-login']")
        await page.wait_for_url("**/")

        # Verify attention dashboard sections
        blocked_section = page.locator("[data-testid='section-blocked']")
        stale_section = page.locator("[data-testid='section-stale']")

        await expect(blocked_section).to_be_visible()
        await expect(blocked_section).to_contain_text("Implement avatar")  # blocked task

        await expect(stale_section).to_be_visible()
        await expect(stale_section).to_contain_text("Fix pagination")  # stale task

        # Drill down into blocked task
        await blocked_section.locator("[data-testid='task-card']").first.click()
        await page.wait_for_url("**/tasks/*")

        # Answer clarification
        await page.fill("[data-testid='clarification-answer']", "Max size: 5MB")
        await page.click("[data-testid='submit-answer']")
        await expect(page.locator("[data-testid='flash-message']")).to_contain_text("resolved")

        # Go back to dashboard
        await page.goto("http://localhost:35173/")

        # Release stale task
        stale_card = stale_section.locator("[data-testid='task-card']").first
        await stale_card.locator("[data-testid='release-button']").click()
        await page.click("[data-testid='confirm-release']")

        # Verify stale section updates
        await expect(stale_section.locator("[data-testid='task-card']")).to_have_count(0)

        # Check audit log
        await page.click("[data-testid='nav-audit']")
        await expect(page.locator("[data-testid='audit-entry']").first).to_contain_text("release")
```

## 5. Fixtures и Setup

### 5.1 Seeded Data

```python
# tests/e2e/conftest.py
@pytest.fixture
async def seeded_data(db_session, user_factory, project_factory, task_factory):
    admin = await user_factory(email="admin@example.com", role="admin")
    project = await project_factory(name="E2E Project", owner=admin)

    # Blocked task (with pending clarification)
    blocked_task = await task_factory(
        project=project, title="Implement avatar", status="blocked"
    )
    await clarification_factory(task=blocked_task, question="Max file size?")

    # Stale task
    stale_task = await task_factory(
        project=project, title="Fix pagination", status="claimed",
        agent_id="agent-1",
        last_heartbeat_at=datetime.utcnow() - timedelta(minutes=10)
    )

    # Active task
    active_task = await task_factory(
        project=project, title="Add logging", status="in_progress",
        agent_id="agent-2"
    )

    return {"admin": admin, "project": project, "blocked": blocked_task, "stale": stale_task}
```

### 5.2 Browser Config

```python
# conftest.py
@pytest.fixture(scope="session")
async def browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()
```

## 6. Запуск

```bash
# Все E2E тесты
make test-e2e

# Только flow 1
pytest tests/e2e/test_first_run_flow.py -v

# С видимым браузером (debug)
HEADED=1 pytest tests/e2e/ -v

# С видео (для CI)
pytest tests/e2e/ --video=on

# С скриншотами при падении
pytest tests/e2e/ --screenshot=on
```

## 7. CI интеграция

```yaml
# .gitlab-ci.yml
test:e2e:
  stage: test
  image: mcr.microsoft.com/playwright:latest
  services:
    - postgres:16-alpine
    - redis:7-alpine
  script:
    - make test-e2e
  artifacts:
    when: on_failure
    paths:
      - tests/e2e/screenshots/
      - tests/e2e/videos/
    expire_in: 7 days
```
