# SaaS Readiness — UPCP v2

> Related: [UPCP v2 PRD](./upcp-v2.md) | Milestone: future

## 1. Overview

This document describes architectural decisions for the future SaaS version of UPCP. SaaS is not implemented in v2, but the architecture must allow for it.

## 2. Current SaaS-Readiness Decisions

### 2.1 Organization Model

Organization is created from day one:
- `id`, `name`, `slug`, `is_default`
- Standalone: a single default org is created automatically
- SaaS: each organization is a separate tenant

### 2.2 Multi-user Support

- User + Membership + RBAC — from M7
- Roles: Owner, Admin, Member, Viewer
- Scope bindings: global, organization, project

### 2.3 Feature Flags

Future SaaS features are controlled via feature flags:

| Flag | Default | Description |
|------|---------|-------------|
| `public_registration` | false | Open registration |
| `email_verification` | false | Email verification |
| `invitations` | false | User invitations |
| `oidc` | false | External authentication |
| `multi_org` | false | Multiple organizations |
| `billing` | false | Payments and subscriptions |
| `webhooks` | false | External webhooks |

### 2.4 Data Isolation

In standalone — everything in one database, one org.
In SaaS — two options:

1. **Shared database, org-scoped queries** (v2 default): all orgs in one table, isolation via `org_id` in every query
2. **Schema-per-org** (future): PostgreSQL schemas for isolation

### 2.5 Rate Limiting

Rate limiting via Redis with org-level quotas:
- Free tier: 1000 req/day
- Pro tier: 10000 req/day
- Enterprise: custom

## 3. Not Done in v2

- Billing and subscriptions
- Usage metering
- Stripe/integration
- Public registration UI
- Email sending (SMTP ready, but not implemented)
- OIDC UI
- Multi-region
- Advanced org hierarchy (parent/child orgs)

## 4. Migration Path (Standalone → SaaS)

1. v2: standalone with Organization model
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
