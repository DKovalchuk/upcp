# Git Conventions

## Branch naming

```text
task/UPC-<task_number>-short-slug
feature/UPC-F<feature_number>-short-slug
fix/UPC-<task_number>-short-slug
docs/UPC-<task_number>-short-slug
chore/UPC-<task_number>-short-slug
```

Examples:

```text
task/UPC-1-scaffold-health
feature/UPC-F1-bootstrap
fix/UPC-12-health-timeout
```

## Commit format

```text
<type>(<scope>): <summary> [UPC-<task_number>]
```

Examples:

```text
chore(repo): scaffold project [UPC-1]
test(health): add health smoke test [UPC-1]
feat(health): add health endpoint [UPC-1]
docs(agents): clarify token economy [UPC-1]
```

## Rules

- one task per branch where practical;
- one logical change per commit;
- no secrets in commits;
- no generated artifacts in commits;
- do not push automatically unless explicitly allowed;
- do not modify remote project repositories from UPCP runtime.
