# Testing Standards

## Test naming

```text
test_<behavior>_<condition>_<expected>
```

Examples:

```python
test_health_returns_ok
test_create_project_with_duplicate_slug_fails
test_task_done_fails_when_dod_not_passed
```

## Test structure

Use Arrange-Act-Assert.

```python
def test_example() -> None:
    # arrange
    ...

    # act
    ...

    # assert
    ...
```

## Pyramid

```text
unit tests       70%
integration      20%
e2e/smoke        10%
```

## Rules

- tests must be deterministic;
- no real network calls in unit tests;
- no real secrets;
- use fixtures;
- use in-memory or test DB for integration;
- truncate long outputs;
- prefer fast feedback.

## Commands

```bash
make test
make lint
make typecheck
```
