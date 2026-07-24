# AGENTS.md — UPCP AI Agent Operating Rules

This file is the primary operating manual for AI coding agents.

It must be treated as a stable cached prefix.
Do not rewrite this file during routine tasks.

## 1. Prime Directive

You are working on UPCP — Universal Project Control Plane.

You must always optimize for:

1. Correctness.
2. Small reversible changes.
3. Token efficiency.
4. Test evidence.
5. Clear traceability.
6. Production-grade habits from day one.

You are not allowed to:

- implement large features without a task file;
- add production code without a failing test, except pure scaffolding;
- silently change architecture, public API, DB schema, auth, or security;
- dump whole repositories into context;
- store secrets in code, docs, logs, tests, or prompts;
- mark a task done without evidence.

## 2. Mandatory Reading Order

For any task, read only what is necessary.

Default order:

1. This file: `AGENTS.md`
2. `PROJECT_STATUS.md`
3. Current task file: `tasks/TASK-XXXX-*.md`
4. Related spec file: `specs/SPEC-XXXX-*.md`
5. Only then, if blocked:
   - relevant docs from `docs/INDEX.md`
   - only the specific files needed for implementation

Do not read all docs.
Do not read all source files.
Use search and targeted reads.

## 3. Token Economy Rules

These rules are mandatory.

### 3.1 Context discipline

- Keep active context as small as possible.
- Prefer reading interfaces, schemas, tests, and error messages.
- Do not read entire files if only a symbol is needed.
- Use `rg`, `ls`, `find`, or equivalent search tools first.
- Read a file only if you must modify it or need its contract.
- Prefer small diffs over full file rewrites.
- Do not paste long logs; truncate to the relevant 30–50 lines.
- Do not repeat large context in answers.

### 3.2 File size discipline

- Markdown docs should usually be <= 250 lines.
- Code files should usually be <= 300 lines.
- Test files should usually be <= 300 lines.
- If a file grows too large, create a refactor task.
- Do not perform large refactors inside a feature task unless explicitly required.

### 3.3 Cache-friendly behavior

This project assumes models with prefix caching, including:

- MiMo-V2.5
- DeepSeek-V4 Flash
- Pro variants for audit/critical work

To benefit from cache:

- Keep `AGENTS.md` stable.
- Keep core docs stable.
- Put dynamic data at the end of prompts.
- Do not reorder stable docs.
- Do not rename docs frequently.
- Use stable IDs: `SPEC-xxxx`, `TASK-xxxx`, `UPC-Fxx`, `UPC-xxx`.
- Use small task files instead of huge combined prompts.

### 3.4 Task context pack

For routine implementation, prefer this context shape:

```text
AGENTS.md              stable
current task file      dynamic
related spec           only if needed
interface snippets     only if needed
failing test output    truncated
```

Avoid:

```text
all docs
all source files
full docker files
full dependency tree
long history
```

## 4. Spec Flow

Every non-trivial change starts with a spec.

Flow:

```text
Idea
→ Spec
→ Optional Design
→ Task decomposition
→ Failing tests
→ Implementation
→ Verification
→ Review
→ Done
```

Rules:

- A feature must have a spec file in `specs/`.
- A task must reference a spec or parent task.
- Small tasks may use the task file as a mini-spec.
- Critical changes require a full spec and Pro-level review.
- If requirements are unclear, stop and create a clarification task.

## 5. DDD Rules

UPCP is a modular monolith organized by bounded contexts.

Main contexts:

```text
health
shared
projects
structure      # components, modules
delivery       # features, tasks
quality        # DoD, acceptance criteria
gitread        # read-only git integration
reporting
llm
audit
mcp
api
```

Rules:

- Respect context boundaries.
- Do not import internal implementation details from another context.
- Prefer explicit services, schemas, and repositories.
- Keep domain logic pure where practical.
- Keep infrastructure adapters separate.
- Avoid cross-context direct DB joins in early tasks unless explicitly allowed.
- Use ubiquitous language from docs.

## 6. TDD Rules

TDD is mandatory for behavior-changing code.

Cycle:

```text
Red
→ Green
→ Refactor
```

Rules:

- Write a failing test first.
- Implement the minimum code to pass.
- Refactor only after tests pass.
- Do not add speculative abstractions.
- Every bugfix must start with a regression test.
- Scaffolding files may be created without tests, but must be validated by a smoke test or command.
- Do not mark done without passing tests.

## 7. Definition of Done

A task is done only if:

- acceptance criteria are satisfied;
- failing test existed before implementation, where applicable;
- tests pass;
- lint passes;
- type check passes where configured;
- docs affected by the change are updated;
- no secrets are introduced;
- task file status is updated;
- `PROJECT_STATUS.md` is updated;
- evidence is available: test output, command output, or artifact.

## 8. Model Routing

Use the cheapest sufficient model.

Routine models:

- MiMo-V2.5
- DeepSeek-V4 Flash

Use routine models for:

- small tasks;
- CRUD;
- tests;
- docs;
- simple bugfixes;
- refactors with clear tests;
- UI component tweaks;
- repetitive implementation.

Use Pro models for:

- architecture review;
- security review;
- DB schema changes;
- auth/RBAC changes;
- public API contract changes;
- DDD boundary changes;
- complex debugging after two failed routine attempts;
- critical migrations;
- LLM redaction/security logic;
- audit after milestone completion.

If a routine model fails twice on the same issue, stop and either:

1. decompose the task; or
2. escalate to Pro model.

## 9. Stop Conditions

Stop and report if:

- task is ambiguous;
- required context is missing;
- change touches security, auth, permissions, or secrets;
- DB migration is required;
- public API contract must change;
- tests cannot be written;
- context budget is exceeded;
- more than two failed fix attempts occur;
- a file is too large and needs decomposition.

## 10. Output Discipline

Final response must be concise.

Prefer:

```text
Summary
Files changed
Tests added
Commands run
Evidence
Next task
Blockers
```

Do not output entire files unless explicitly requested.
Do not output long explanations unless debugging.
