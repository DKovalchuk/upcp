# Permission Matrix Tests — Спецификация

> Проект: UPCP | Фреймворк: pytest | RBAC: owner, admin, member, viewer, agent

## 1. Обзор

Permission matrix tests проверяют, что каждая роль имеет ровно те права, которые ей положено, и не имеет доступа к тому, что запрещено.

## 2. Роли и их права

### 2.1 Owner
- Всё в своей организации
- Управление billing (future)
- Удаление организации
- Назначение admin

### 2.2 Admin
- CRUD проектов в организации
- Управление участниками (кроме owner)
- Настройка проектов
- Просмотр audit log
- Force release claims

### 2.3 Member
- CRUD задач в своих проектах
- Просмотр задач, evidence, reviews
- Создание review
- Отправка сообщений агентам

### 2.4 Viewer
- Только чтение: проекты, задачи, evidence
- Не может создавать/изменять/удалять

### 2.5 Agent
- Claim/release задач (назначенных)
- Heartbeat
- Evidence upload (к своей задаче)
- Inbox чтение
- Не может: создавать проекты, управлять пользователями

## 3. Матрица разрешений

| Resource / Action | Owner | Admin | Member | Viewer | Agent |
|-------------------|-------|-------|--------|--------|-------|
| **Organization** |
| org.create | ✅ | ❌ | ❌ | ❌ | ❌ |
| org.update | ✅ | ✅ | ❌ | ❌ | ❌ |
| org.delete | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Members** |
| member.invite | ✅ | ✅ | ❌ | ❌ | ❌ |
| member.remove | ✅ | ✅ | ❌ | ❌ | ❌ |
| member.change_role | ✅ | ✅* | ❌ | ❌ | ❌ |
| **Project** |
| project.create | ✅ | ✅ | ❌ | ❌ | ❌ |
| project.read | ✅ | ✅ | ✅ | ✅ | ✅ |
| project.update | ✅ | ✅ | ❌ | ❌ | ❌ |
| project.delete | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Task** |
| task.create | ✅ | ✅ | ✅ | ❌ | ❌ |
| task.read | ✅ | ✅ | ✅ | ✅ | ✅ |
| task.update | ✅ | ✅ | ✅ | ❌ | ❌ |
| task.delete | ✅ | ✅ | ✅ | ❌ | ❌ |
| task.claim | ❌ | ❌ | ❌ | ❌ | ✅ |
| task.release | ❌ | ❌ | ❌ | ❌ | ✅ |
| task.heartbeat | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Evidence** |
| evidence.create | ✅ | ✅ | ✅ | ❌ | ✅** |
| evidence.read | ✅ | ✅ | ✅ | ✅ | ✅ |
| evidence.accept | ✅ | ✅ | ✅ | ❌ | ❌ |
| evidence.reject | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Review** |
| review.submit | ✅ | ✅ | ✅ | ❌ | ✅*** |
| review.approve | ✅ | ✅ | ✅ | ❌ | ❌ |
| review.request_changes | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Playbook** |
| playbook.read | ✅ | ✅ | ✅ | ✅ | ✅ |
| playbook.update | ✅ | ✅ | ❌ | ❌ | ❌ |
| **API Keys** |
| api_key.create | ✅ | ✅ | ❌ | ❌ | ❌ |
| api_key.revoke | ✅ | ✅ | ❌ | ❌ | ❌ |
| api_key.list | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Audit** |
| audit.read | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Settings** |
| settings.update | ✅ | ✅ | ❌ | ❌ | ❌ |

> *Admin не может менять роль owner
> **Agent может evidence.create только для своей claimed задачи
> ***Agent может review.submit только для своей задачи с полным evidence

## 4. Структура тестов

```python
# tests/permissions/test_permission_matrix.py
import pytest
from httpx import AsyncClient

ROLES = ["owner", "admin", "member", "viewer", "agent"]

class PermissionTest:
    """Базовый класс для matrix тестов."""

    @pytest.fixture(params=ROLES)
    def role(self, request):
        return request.param

    @pytest.fixture
    def auth_headers(self, role, user_factory, api_key_factory):
        if role == "agent":
            key = await api_key_factory(role="agent")
            return {"Authorization": f"ApiKey {key.key}"}
        user = await user_factory(role=role)
        token = create_access_token(user)
        return {"Authorization": f"Bearer {token}"}


class TestOrganizationPermissions(PermissionTest):

    PERMISSIONS = {
        "owner": ["create", "read", "update", "delete"],
        "admin": ["read", "update"],
        "member": ["read"],
        "viewer": ["read"],
        "agent": [],
    }

    async def test_org_create(self, client, auth_headers, role):
        if "create" in self.PERMISSIONS[role]:
            resp = await client.post("/api/v1/orgs", json={"name": "test"}, headers=auth_headers)
            assert resp.status_code == 201
        else:
            resp = await client.post("/api/v1/orgs", json={"name": "test"}, headers=auth_headers)
            assert resp.status_code in (403, 401)

    async def test_org_read(self, client, auth_headers, role, org):
        if "read" in self.PERMISSIONS[role]:
            resp = await client.get(f"/api/v1/orgs/{org.id}", headers=auth_headers)
            assert resp.status_code == 200
        else:
            resp = await client.get(f"/api/v1/orgs/{org.id}", headers=auth_headers)
            assert resp.status_code in (403, 401)
```

## 5. Тесты для каждой группы ресурсов

### 5.1 Organization Tests
```
test_org_create_by_owner → 201
test_org_create_by_admin → 403
test_org_create_by_member → 403
test_org_create_by_viewer → 403
test_org_create_by_agent → 403
test_org_update_by_owner → 200
test_org_update_by_admin → 200
test_org_update_by_member → 403
test_org_delete_by_owner → 204
test_org_delete_by_admin → 403
```

### 5.2 Task Tests
```
test_task_create_by_member → 201
test_task_create_by_viewer → 403
test_task_create_by_agent → 403
test_task_claim_by_agent → 200
test_task_claim_by_member → 403
test_task_read_by_viewer → 200
test_task_read_by_unauthenticated → 401
```

### 5.3 Evidence Tests
```
test_evidence_create_by_agent_for_own_task → 201
test_evidence_create_by_agent_for_other_task → 403
test_evidence_accept_by_member → 200
test_evidence_accept_by_agent → 403
test_evidence_read_by_viewer → 200
```

## 6. Cross-project Isolation

```python
class TestCrossProjectIsolation:

    async def test_member_cannot_access_other_project(self, client, auth_headers_member, other_project):
        resp = await client.get(f"/api/v1/projects/{other_project.id}/tasks", headers=auth_headers_member)
        assert resp.status_code == 403

    async def test_agent_cannot_claim_other_project_task(self, client, auth_headers_agent, other_project_task):
        resp = await client.post(f"/api/v1/tasks/{other_project_task.id}/claim", headers=auth_headers_agent)
        assert resp.status_code == 403
```

## 7. Unauthenticated Access

```python
class TestUnauthenticated:

    PUBLIC_ENDPOINTS = [
        ("GET", "/health"),
        ("GET", "/api/v1/docs"),
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/register"),
    ]

    PROTECTED_ENDPOINTS = [
        ("GET", "/api/v1/projects"),
        ("POST", "/api/v1/tasks"),
        ("GET", "/api/v1/orgs"),
    ]

    async def test_public_endpoints_accessible(self, client, method, path):
        resp = await client.request(method, path)
        assert resp.status_code != 401

    async def test_protected_endpoints_require_auth(self, client, method, path):
        resp = await client.request(method, path)
        assert resp.status_code == 401
```

## 8. Запуск

```bash
# Все permission тесты
make test-permissions

# Только определённую роль
pytest tests/permissions/ -k "owner" -v

# Только определённый ресурс
pytest tests/permissions/ -k "task" -v

# С отчётом покрытия
pytest tests/permissions/ --cov=src/upcp/api/permissions --cov-report=html
```

## 9. Coverage Matrix Report

Тест генерирует отчёт в формате матрицы:

```
Permission Matrix Report
========================
Resource      Action       Owner  Admin  Member  Viewer  Agent
────────────────────────────────────────────────────────────────
Organization  create       PASS   PASS   PASS    PASS    PASS
Organization  update       PASS   PASS   PASS    PASS    PASS
Task          claim        PASS   PASS   PASS    PASS    PASS
...
────────────────────────────────────────────────────────────────
Total: 45/45 tests passed
```
