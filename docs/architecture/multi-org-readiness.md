# Multi-Org Readiness — UPCP v2

## Overview

UPCP v2 is designed as a single-org self-hosted application with readiness for multi-tenant SaaS mode. The Organization model architecture allows a painless transition from standalone to multi-org.

---

## Organization Model

### Current Architecture

```
┌──────────────────────────────────────────┐
│              Organization                 │
│  (single organization at bootstrap)       │
│                                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │  User   │  │ Project │  │  Agent  │  │
│  │(member) │  │         │  │         │  │
│  └─────────┘  └─────────┘  └─────────┘  │
│                                           │
└──────────────────────────────────────────┘
```

### Target SaaS Architecture

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

### Current Model

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

### Model

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

### Organization Roles

| Role | Description | Assigned By |
|------|-------------|-------------|
| `owner` | Full control | Org creator (auto) |
| `admin` | Manage users, projects, agents | Owner |
| `member` | Work with projects, tasks | Admin |
| `viewer` | Read-only access | Admin |

### Scope Isolation

```python
# All queries are automatically filtered by organization_id
class OrgScopedRepository:
    """Base repository with org scope."""

    def __init__(self, session: AsyncSession, org_id: UUID):
        self.session = session
        self.org_id = org_id

    def _scope_query(self, stmt):
        return stmt.where(self.model.organization_id == self.org_id)
```

---

## Default Org Bootstrap

### At First Boot

```python
async def bootstrap_organization(db: AsyncSession) -> Organization:
    """Creates default organization at first boot."""

    # Check if an organization already exists
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

    # Create system roles
    await create_system_roles(db, org.id)

    return org
```

### First User

```python
async def bootstrap_first_user(
    db: AsyncSession,
    org: Organization,
    email: str,
    password: str,
) -> User:
    """The first user automatically becomes owner."""

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

**Purpose:** Allow new user registration without an invitation.

**Default:** `false` (self-hosted)

**When enabled:**
- `POST /auth/register` accepts requests without an invite token
- Requires `email_verification` for activation
- New users receive the `member` role in the default org

```python
@router.post("/auth/register")
async def register(body: RegisterRequest, org: Organization = Depends(get_org)):
    if not org.settings["features"]["public_registration"]:
        raise HTTPException(403, "Public registration is disabled")

    # ...
```

### `email_verification`

**Purpose:** Require email confirmation upon registration.

**Default:** `false` (self-hosted)

**When enabled:**
- A verification email is sent upon registration
- Users cannot log in until confirmed
- Verification token lives for 24 hours

```python
@router.post("/auth/verify-email")
async def verify_email(body: VerifyEmailRequest):
    # Verify the token, activate the user
    ...
```

### `invitations`

**Purpose:** Manage organization invitations.

**Default:** `true`

**When enabled:**
- Owner/Admin can invite by email
- Invite token lives for 7 days
- Invitations are tied to a specific role

```python
@router.post("/organizations/{org_id}/invitations")
async def create_invitation(
    org_id: UUID,
    body: InvitationRequest,
    user: User = Depends(get_current_user),
    membership: Membership = Depends(require_admin),
):
    # Create invitation, send email
    ...
```

### `oidc_enabled`

**Purpose:** Connect external OIDC providers (Google, GitLab, Keycloak).

**Default:** `false`

**When enabled:**
- A "Sign in with ..." button appears on the login page
- OIDC users are automatically created/linked
- JIT provisioning: user is created on first login

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

**Purpose:** Payment system integration for SaaS.

**Default:** `false`

**When enabled:**
- Org settings include a billing plan
- Limits depend on the plan
- Webhook from the payment system updates subscriptions

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

- [x] Organization model with settings
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

1. **Repository level:** `_scope_query` filter
2. **Service level:** `current_org` dependency injection
3. **Middleware level:** JWT contains `org_id`, middleware verifies
4. **Database level:** Row-Level Security (optional, for SaaS)

### RLS (Row-Level Security) — for SaaS

```sql
-- Enable RLS on the projects table
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Policy: user sees only projects belonging to their organization
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
