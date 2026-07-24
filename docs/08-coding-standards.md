# Coding Standards

## Python

- Python 3.12.
- Strict typing.
- Pydantic schemas for API input/output.
- Small modules.
- One responsibility per module.
- Explicit error handling.
- Structured logging.
- No secrets in code.
- No print statements in app code.
- Use `logging` or structured logger.
- Prefer pure functions where practical.
- Avoid deep inheritance.
- Avoid global mutable state.

## File limits

- code file: usually <= 300 lines;
- test file: usually <= 300 lines;
- markdown doc: usually <= 250 lines.

## Naming

- English identifiers.
- snake_case for functions/variables.
- PascalCase for classes.
- UPPER_SNAKE_CASE for constants.
- stable task/spec IDs in docs and commits.

## API

- versioned under `/api/v1`;
- JSON responses;
- explicit schemas;
- pagination for lists;
- problem-like error responses;
- idempotency keys for mutating operations where needed.

## Errors

Use typed error taxonomy:

```text
validation_error
not_found
permission_denied
conflict
dod_failed
approval_required
external_git_error
external_ci_error
internal_error
```

## Logging

Log structured events:

```text
event
project_id
entity_type
entity_id
actor_type
actor_id
error_code
```

Do not log:

- secrets;
- tokens;
- passwords;
- full LLM prompts by default;
- sensitive personal data.
