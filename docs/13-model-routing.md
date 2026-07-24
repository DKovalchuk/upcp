# Model Routing

Use the cheapest sufficient model.

## Routine models

Use:

- MiMo-V2.5
- DeepSeek-V4 Flash

For:

- small implementation tasks;
- tests;
- docs;
- simple bugfixes;
- small refactors;
- UI component work;
- repetitive CRUD;
- validation logic;
- report templates.

## Pro models

Use Pro variants for:

- architecture review;
- security review;
- DB schema changes;
- migrations;
- auth/RBAC;
- permission model;
- secret handling;
- LLM redaction;
- public API contract changes;
- DDD boundary changes;
- performance issues;
- complex debugging;
- milestone audit.

## Escalation rules

Escalate to Pro if:

- routine model fails twice on same issue;
- task touches critical modules;
- context is too large for routine model;
- change is irreversible;
- security or data integrity is involved.

## Critical modules

These require Pro review:

```text
auth
permissions
audit
db migrations
secret handling
LLM redaction
API contract changes
quality gate logic
```
