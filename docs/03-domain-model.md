# Domain Model

> **Source of truth**: `docs/architecture/data-model.md` for full field definitions
> **Source of truth**: `backend/app/*/models.py` for actual implementation

Core entities (as implemented):

```text
Organization
User
Membership
Agent
AgentToken
Project
Component
Module
Feature
Task
Subtask
TaskClaim
Heartbeat
ClarificationRequest
TaskDependency
AcceptanceCriterion
DoDItem
Evidence
ReviewRound
ReviewFinding
Notification
Report
AuditEvent
GitProvider
GitBranch
GitCommit
GitLink
```

Primary structural hierarchy:

```text
Project
└── Component
    └── Module
```

Primary delivery hierarchy:

```text
Project
└── Feature
    └── Task
        ├── Subtask
        ├── AcceptanceCriterion
        ├── DoDItem
        ├── Evidence
        ├── ClarificationRequest
        ├── TaskClaim → Heartbeat
        └── ReviewRound → ReviewFinding
```

Flexible links:

```text
Task
  → feature
  → component (optional)
  → module (optional)
  → git links

Feature
  → primary_component (optional)
```

Identity hierarchy:

```text
Organization
├── User (via Membership)
├── Agent → AgentToken
└── Project
```

> **NOTE**: Earlier drafts referenced `Spec`, `GitRepo`, `GitPullRequest` entities.
> These do not exist in the implementation. `GitRepo` was replaced by `GitProvider`.
> `Spec` and `GitPullRequest` were never implemented.
