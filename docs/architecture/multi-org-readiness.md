# Multi-Org Readiness — UPCP v2

## Обзор

UPCP v2 спроектирован как single-org self-hosted приложение с готовностью к мультитенантному SaaS-режиму. Архитектура Organization модели позволяет безболезненно перейти от standalone к multi-org.

---

## Organization Model

### Текущая архитектура

```
┌──────────────────────────────────────────┐
│              Organization                 │
│  (одна организация при bootstrap)        │
│                                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │  User   │  │ Project │  │  Agent  │  │
│  │(member) │  │         │  │         │  │
│  └─────────┘  └─────────┘  └─────────┘  │
│                                           │
└──────────────────────────────────────────┘
```

### Target SaaS архитектура

```
┌─────────────────────────────────────────────────┐
│                  Platform                         │
│                                                   │
│  ┌───────────────┐    ┌───────────────┐          │
│  │ Organization A │    │ Organization B │   ...   │
│  │ (Acme Corp)    │    │ (Beta Inc)    │          │
│  │                │    │               │          │
│  │ ┌────┐ ┌────┐ │    │ ┌────┐ ┌───┐ │          │
│  │ │User│ │Proj│ │    │ │User│ │Pro│ │          │
│  │ └────┘ └────┘ │    │ └────┘ └───┘ │          │
│  └───────────────┘    └───────────────┘          │
│                                                   │
└─────────────────────────────────────────────────┘
```

### Текущая модель

```python
class Organization(BaseModel):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

### Settings (JSONB)

```json
{
    "features": {
        "public_registration": false,
        "email_verification": false,
        "invitations": true,
        "oidc_enabled": false,
        "billing_enabled": false
    },
    "limits": {
        "max_users": null,
        "max_projects": null,
        "max_agents": null,
        "max_tasks_per_project": null
    },
    "defaults": {
        "review_policy": "human_only",
        "heartbeat_timeout_sec": 120,
        "task_expiry_days": 14
    }
}
```

---

## Membership

### Модель

```python
class Membership(BaseModel):
    __tablename__ = "memberships"

    id: Mapped[UUID]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"))
    invited_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    joined_at: Mapped[datetime]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

### Роли в организации

| Роль | Описание | Назначается |
|------|----------|------------|
| `owner` | Полный контроль | Создатель org (auto) |
| `admin` | Управление пользователями, проектами, агентами | Owner |
| `member` | Работа с проектами, задачами | Admin |
| `viewer` | Только чтение | Admin |

### Scope изоляция

```python
# Все запросы автоматически фильтруются по organization_id
class OrgScopedRepository:
    """Базовый репозиторий с org scope."""

    def __init__(self, session: AsyncSession, org_id: UUID):
        self.session = session
        self.org_id = org_id

    def _scope_query(self, stmt):
        return stmt.where(self.model.organization_id == self.org_id)
```

---

## Default Org Bootstrap

### При первом запуске

```python
async def bootstrap_organization(db: AsyncSession) -> Organization:
    """Создаёт default organization при первом запуске."""

    # Проверяем, есть ли уже организация
    existing = await db.scalar(select(Organization).limit(1))
    if existing:
        return existing

    org = Organization(
        name="Default",
        slug="default",
        settings={
            "features": {
                "public_registration": False,
                "email_verification": False,
                "invitations": True,
                "oidc_enabled": False,
                "billing_enabled": False,
            }
        },
    )
    db.add(org)
    await db.flush()

    # Создаём системные роли
    await create_system_roles(db, org.id)

    return org
```

### Первый пользователь

```python
async def bootstrap_first_user(
    db: AsyncSession,
    org: Organization,
    email: str,
    password: str,
) -> User:
    """Первый пользователь автоматически становится owner."""

    user = User(email=email, display_name="Admin")
    user.password_hash = hash_password(password)
    db.add(user)
    await db.flush()

    owner_role = await get_role_by_name(db, org.id, "owner")
    membership = Membership(
        user_id=user.id,
        organization_id=org.id,
        role_id=owner_role.id,
    )
    db.add(membership)

    return user
```

---

## Feature Flags

### `public_registration`

**Purpose:** Разрешить регистрацию новых пользователей без приглашения.

**Default:** `false` (self-hosted)

**When enabled:**
- `POST /auth/register` принимает запросы без invite token
- Требует `email_verification` для активации
- Новый пользователь получает роль `member` в default org

```python
@router.post("/auth/register")
async def register(body: RegisterRequest, org: Organization = Depends(get_org)):
    if not org.settings["features"]["public_registration"]:
        raise HTTPException(403, "Public registration is disabled")

    # ...
```

### `email_verification`

**Purpose:** Требовать подтверждение email при регистрации.

**Default:** `false` (self-hosted)

**When enabled:**
- При регистрации отправляется verification email
- Пользователь не может войти до подтверждения
- Verification token живёт 24 часа

```python
@router.post("/auth/verify-email")
async def verify_email(body: VerifyEmailRequest):
    # Проверяем token, активируем пользователя
    ...
```

### `invitations`

**Purpose:** Управление приглашениями в организацию.

**Default:** `true`

**When enabled:**
- Owner/Admin может пригласить по email
- Invite token живёт 7 дней
- Приглашение привязано к конкретной роли

```python
@router.post("/organizations/{org_id}/invitations")
async def create_invitation(
    org_id: UUID,
    body: InvitationRequest,
    user: User = Depends(get_current_user),
    membership: Membership = Depends(require_admin),
):
    # Создаём приглашение, отправляем email
    ...
```

### `oidc_enabled`

**Purpose:** Подключение внешних OIDC-провайдеров (Google, GitLab, Keycloak).

**Default:** `false`

**When enabled:**
- Появляется кнопка «Войти через ...» на странице логина
- OIDC user автоматически создаётся/привязывается
- JIT provisioning: пользователь создаётся при первом входе

```python
@router.get("/auth/oidc/{provider}/authorize")
async def oidc_authorize(provider: str, org: Organization = Depends(get_org)):
    if not org.settings["features"]["oidc_enabled"]:
        raise HTTPException(403, "OIDC is not enabled")
    # Redirect to OIDC provider
    ...

@router.get("/auth/oidc/{provider}/callback")
async def oidc_callback(provider: str, code: str, state: str):
    # Exchange code, find or create user
    ...
```

### `billing_enabled`

**Purpose:** Интеграция с платёжной системой для SaaS.

**Default:** `false`

**When enabled:**
- Org settings включают billing plan
- Limits зависят от плана
- Webhook от платёжной системы обновляет подписку

```python
# Future implementation
class BillingPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

PLAN_LIMITS = {
    BillingPlan.FREE: {"max_users": 5, "max_projects": 3, "max_agents": 2},
    BillingPlan.PRO: {"max_users": 50, "max_projects": 20, "max_agents": 10},
    BillingPlan.ENTERPRISE: {"max_users": None, "max_projects": None, "max_agents": None},
}
```

---

## Migration Path: Self-Hosted → SaaS

### Phase 1: Multi-Org Foundation (v2.0)

- [x] Organization model с settings
- [x] Membership model
- [x] Org-scoped queries
- [x] Default org bootstrap
- [ ] Invitations system

### Phase 2: Auth Enhancement (v2.1)

- [ ] Public registration
- [ ] Email verification
- [ ] OIDC integration
- [ ] Password reset flow
- [ ] Session management UI

### Phase 3: Limits & Billing (v2.2)

- [ ] Plan-based limits enforcement
- [ ] Usage tracking
- [ ] Billing webhook handler
- [ ] Stripe/LemonSqueezy integration

### Phase 4: SaaS Operations (v2.3)

- [ ] Admin panel (platform-level)
- [ ] Org management (create, suspend, delete)
- [ ] Cross-org analytics
- [ ] Onboarding flow

---

## Data Isolation

### Strategy: Shared Database, Row-Level Isolation

```
┌─────────────────────────────────────────────────┐
│                PostgreSQL                        │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ organizations (shared)                    │   │
│  │  org_A | org_B | org_C                    │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ projects (org_id FK)                      │   │
│  │  WHERE org_id = :current_org              │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ tasks, agents, etc. (org-scoped)          │   │
│  │  All queries include org_id filter         │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Enforcement Levels

1. **Repository level:** `_scope_query` фильтр
2. **Service level:** `current_org` dependency injection
3. **Middleware level:** JWT содержит `org_id`, middleware проверяет
4. **Database level:** Row-Level Security (optional, для SaaS)

### RLS (Row-Level Security) — для SaaS

```sql
-- Включаем RLS на таблице projects
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Политика: пользователь видит только проекты своей организации
CREATE POLICY org_isolation ON projects
    USING (organization_id = current_setting('app.current_org_id')::uuid);
```

---

## Configuration Matrix

| Feature | Self-Hosted Default | SaaS Default |
|---------|-------------------|-------------|
| public_registration | `false` | `false` (invite-only) |
| email_verification | `false` | `true` |
| invitations | `true` | `true` |
| oidc_enabled | `false` | optional |
| billing_enabled | `false` | `true` |
| max_users | `null` (unlimited) | plan-based |
| max_projects | `null` (unlimited) | plan-based |
| RLS | disabled | enabled |
