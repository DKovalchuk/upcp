You are Qwen CLI working inside the UPCP repository.

Your job is to implement the current task using Spec Flow, DDD, and TDD.

Follow `AGENTS.md` strictly.

Do not read all documentation.
Do not read all source files.
Do not implement anything outside the current task.

Current task:

```text
tasks/TASK-0001-scaffold-health.md
```

Allowed context:

```text
AGENTS.md
PROJECT_STATUS.md
tasks/TASK-0001-scaffold-health.md
specs/SPEC-0001-bootstrap.md
backend/app/__init__.py
backend/tests/__init__.py
backend/requirements.txt
pyproject.toml
Makefile
docker-compose.yml
```

If you need more context, use search first and read only the minimal required file.

Implementation rules:

1. Use TDD.
2. First create a failing test.
3. Run the test and confirm failure.
4. Implement the minimum code required.
5. Run tests again and confirm pass.
6. Run lint and typecheck.
7. Validate Docker Compose config.
8. Update task status.
9. Update PROJECT_STATUS.md.
10. Stop.

Commands to use:

```bash
make test
make lint
make typecheck
docker compose config
```

If Docker daemon is unavailable, do not fail the task.
Instead:

- validate `docker compose config` if possible;
- note the limitation in `PROJECT_STATUS.md`;
- continue.

Expected endpoint:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "upcp-backend"
}
```

Do not add:

- database models;
- auth;
- frontend;
- MCP;
- LLM;
- Git integration;
- extra dependencies unless required for the task.

Token economy:

- keep final summary under 30 lines;
- do not output whole files unless necessary;
- do not paste long logs;
- use small diffs;
- stop if context becomes too large.

If blocked:

- write the blocker in `PROJECT_STATUS.md`;
- create a small clarification task if needed;
- stop.

If git repository exists, create a local commit:

```text
chore(repo): scaffold health endpoint [UPC-1]
```

Do not push.

Final output must contain:

```text
Summary
Files changed
Tests added
Commands run
Evidence
Next task
Blockers
```
