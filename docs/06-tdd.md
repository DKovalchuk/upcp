# TDD Rules

TDD is mandatory for behavior-changing code.

## Cycle

```text
1. Write failing test.
2. Run test and confirm failure.
3. Write minimal implementation.
4. Run test and confirm pass.
5. Refactor if needed.
6. Run lint/typecheck/tests.
```

## Test types

- unit tests: pure logic, services, validators;
- integration tests: API + DB;
- smoke tests: app starts, health works;
- acceptance tests: user-visible behavior.

## Rules

- No production behavior without failing test.
- Bugfix requires regression test.
- Do not test implementation details.
- Prefer testing public contracts.
- Use fixtures for repeated setup.
- Keep tests deterministic.
- Avoid network calls in unit tests.
- Use fakes for time, randomness, external services.

## Evidence

A task must include at least one of:

- pytest output;
- make test output;
- curl smoke output;
- docker compose validation output.
