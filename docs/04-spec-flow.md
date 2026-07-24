# Spec Flow

All non-trivial work follows Spec Flow.

```text
Idea
→ Spec
→ Optional Design
→ Tasks
→ Failing Tests
→ Implementation
→ Verification
→ Review
→ Done
```

## Spec file

Location:

```text
specs/SPEC-XXXX-short-name.md
```

Minimum spec content:

```markdown
# SPEC-XXXX

Status: draft | review | approved
Owner:
Related features:
Related tasks:

## Problem

## Goal

## Non-goals

## Requirements

## Acceptance Criteria

## Risks

## DoD
```

## Task file

Location:

```text
tasks/TASK-XXXX-short-name.md
```

Minimum task content:

```markdown
# TASK-XXXX

Spec:
Status: backlog | ready | in_progress | blocked | done
Priority:
Model: routine | pro

## Goal

## Non-goals

## Files

## Acceptance Criteria

## Tests

## DoD

## Notes
```

## Rules

- No large feature without spec.
- No implementation task without tests.
- No Done without DoD.
- Unclear task → clarification task.
