# Token Economy Rules

This project is designed for efficient work with:

- MiMo-V2.5
- DeepSeek-V4 Flash
- Pro variants for audit/critical tasks

## Core idea

Do not maximize context.
Minimize sufficient context.

## Prompt structure

Preferred stable prefix:

```text
AGENTS.md
selected stable docs
task template
```

Dynamic suffix:

```text
current task
current status
specific error
specific interface snippet
```

## Context budgets

Approximate targets:

| Work type | Active context target |
|---|---:|
| routine implementation | <= 15k–25k tokens |
| debugging | <= 30k–40k tokens |
| architecture audit | Pro model, curated context |
| full milestone review | Pro model, curated context |

These are targets, not hard limits.

## Mandatory habits

- read only required files;
- use search before reading;
- avoid whole-file dumps;
- avoid whole-repo dumps;
- truncate logs;
- keep files small;
- keep docs small;
- use stable IDs;
- use task files;
- use small diffs;
- do not repeat large text in answers;
- prefer examples over long prose;
- prefer typed contracts over implicit behavior.

## Cache-aware rules

For models with prefix caching:

- keep `AGENTS.md` stable;
- keep core docs stable;
- avoid renaming files often;
- avoid reordering stable docs;
- append decisions instead of rewriting;
- put volatile data last.

## When to stop and decompose

Stop if:

- more than 6 files must be held in active context;
- a file is too large;
- logs exceed useful size;
- the task requires cross-context refactoring;
- the model fails twice on the same issue.

Then create smaller subtasks.
