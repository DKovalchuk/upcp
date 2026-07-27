# E2E Critical Flows — Specification

> Project: UPCP | Tool: Playwright (frontend) + httpx (backend) | Framework: pytest

## 1. Overview

E2E tests cover 3 critical flows that define the core value of UPCP: from task creation to completion, the agent lifecycle, and control through the attention dashboard.

## 2. Flow 1: First-Run → Task Lifecycle

**Goal:** Verify the full "zero user" lifecycle — from registration to completed task.

### 2.1 Preconditions
- Clean DB (or test fixtures)
- Browser not authenticated

### 2.2 Steps

| # | Action | Expected Result |
|---|---------|-------------------|
| 1 | Open `/` | Redirect to `/login` |
| 2 | Click "Register" | Registration form |
| 3 | Fill in email + password | Validation passes |
| 4 | Submit | Redirect to `/setup` (first-run) |
| 5 | Create organization | Org created, redirect to `/projects` |
| 6 | Create project | Project created, redirect to project page |
| 7 | Create task "Implement feature X" | Task in status `open` |
| 8 | Create API key for agent | Key is displayed |
| 9 | (API) Claim task by agent | Status → `claimed` |
| 10 | (API) Heartbeat | Task remains `claimed` |
| 11 | (API) Upload evidence | Evidence attached |
| 12 | (API) Submit review | Status → `in_review` |
| 13 | (UI) See task in "In Review" | Displayed on dashboard |
| 14 | Approve review | Status → `done` |
| 15 | Verify on dashboard | Task in "Recent Done" |

### 2.3 Test

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

**Goal:** Verify the full agent lifecycle with clarification flow.

### 3.1 Preconditions
- Project with task in status `open`
- Agent API key created

### 3.2 Steps

| # | Action | Expected Result |
|---|---------|-------------------|
| 1 | (API) Claim task | Status → `claimed` |
| 2 | (API) Heartbeat with progress | Progress updated |
| 3 | (API) Request clarification | Status → `blocked` |
| 4 | (UI) Blocked notification | Toast notification |
| 5 | (UI) Attention dashboard shows blocked | Blocked section |
| 6 | (UI) Answer clarification | Clarification resolved |
| 7 | (API) Get inbox message | Message with answer |
| 8 | (API) Resume work | Status → `in_progress` |
| 9 | (API) Heartbeat | Stale timer reset |
| 10 | (API) Submit review | Status → `in_review` |

### 3.3 Test

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

**Goal:** Verify that the attention dashboard correctly displays problematic tasks and allows quick action.

### 4.1 Preconditions
- Project with multiple tasks in different statuses
- User is authenticated

### 4.2 Steps

| # | Action | Expected Result |
|---|---------|-------------------|
| 1 | Open `/` | Attention dashboard loaded |
| 2 | Check "Blocked" section | Blocked task is displayed |
| 3 | Check "Stale" section | Stale task is displayed with heartbeat age |
| 4 | Click on blocked task | Detail view opens |
| 5 | Answer clarification | Form submitted |
| 6 | Click "Release" on stale task | Task released → `open` |
| 7 | Verify stale task disappeared from section | Real-time update |
| 8 | Click "Audit Log" | Audit shows actions |

### 4.3 Test

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

## 5. Fixtures and Setup

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

## 6. Running

```bash
# All E2E tests
make test-e2e

# Only flow 1
pytest tests/e2e/test_first_run_flow.py -v

# With visible browser (debug)
HEADED=1 pytest tests/e2e/ -v

# With video (for CI)
pytest tests/e2e/ --video=on

# With screenshots on failure
pytest tests/e2e/ --screenshot=on
```

## 7. CI Integration

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
