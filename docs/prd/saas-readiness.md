# SaaS Readiness — UPCP v2

> Связано: [UPCP v2 PRD](./upcp-v2.md) | Milestone: future

## 1. Обзор

Документ описывает архитектурные решения для будущей SaaS-версии UPCP. В v2 SaaS не реализуется, но архитектура должна это позволять.

## 2. Текущие решения для SaaS-readiness

### 2.1 Organization Model

Organization создается с первого дня:
- `id`, `name`, `slug`, `is_default`
- Standalone: автоматически создаётся одна default org
- SaaS: каждая организация — отдельный租户

### 2.2 Multi-user поддержка

- User + Membership + RBAC — с M7
- Роли: Owner, Admin, Member, Viewer
- Scope bindings: global, organization, project

### 2.3 Feature Flags

Будущие SaaS-фичи управляются через feature flags:

| Flag | Default | Description |
|------|---------|-------------|
| `public_registration` | false | Открытая регистрация |
| `email_verification` | false | Подтверждение email |
| `invitations` | false | Приглашения пользователей |
| `oidc` | false | Внешняя аутентификация |
| `multi_org` | false | Множество организаций |
| `billing` | false | Платежи и подписки |
| `webhooks` | false | Внешние webhook'и |

### 2.4 Data Isolation

В standalone — всё в одной БД, одна org.
В SaaS — два варианта:

1. **Shared database, org-scoped queries** (v2 default): все orgs в одной таблице, изоляция через `org_id` в каждом запросе
2. **Schema-per-org** (future): PostgreSQL schemas для изоляции

### 2.5 Rate Limiting

Rate limiting через Redis с org-level quotas:
- Free tier: 1000 req/day
- Pro tier: 10000 req/day
- Enterprise: custom

## 3. Что НЕ делается в v2

- Billing и subscriptions
- Usage metering
- Stripe/integration
- Public registration UI
- Email sending (SMTP ready, but not implemented)
- OIDC UI
- Multi-region
- Advanced org hierarchy (parent/child orgs)

## 4. Migration Path (Standalone → SaaS)

1. v2: standalone с Organization model
2. v2.1: public registration + email verification
3. v2.2: invitations
4. v3: OIDC
5. v3.1: billing
6. v3.2: multi-region

## 5. Assumptions

1. Standalone deployment is primary use case in v2
2. Organization model exists from day one but only one org is active
3. No billing in v2 — product is free and open-source
4. SaaS version will be a separate deployment mode
5. Data migration from standalone to SaaS will be supported
