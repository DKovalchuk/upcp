# Domain Model

Core entities:

```text
Project
Component
Module
Feature
Task
AcceptanceCriterion
DoDItem
Spec
GitRepo
GitBranch
GitCommit
GitPullRequest
GitLink
AuditEvent
Report
User
Agent
Role
Permission
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
        └── Subtask
```

Flexible links:

```text
Feature
  -> primary_component
  -> linked_components
  -> linked_modules

Task
  -> feature
  -> component
  -> module
  -> git links
```

Optional DDD layer:

```text
Project
└── Domain/Area
    └── Component
        └── Module
```
