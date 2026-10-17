# TASK-0137 — Broken migration chain hotfix (0019/0023) + deploy guards

**Milestone:** ops/CI (incident hotfix)
**Points:** 3
**Spec:** mini-spec (this file); incident 2026-10-17
**Status:** DONE (2026-10-17)

## Context (incident)

Dev/stage backend crash-looped for ~10h (`RestartCount=584`):

```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.DuplicateTable)
relation "ix_task_feature_id" already exists
[SQL: CREATE INDEX ix_task_feature_id ON task (feature_id)]
```

Root cause chain:

- `docker-compose.stage.yml` app runs `alembic upgrade head` on start;
  stage/test DBs sit at `0017`, repo head is `0023`.
- **0019** recreated 17 indexes unconditionally — but 0008 already created
  the same ones on every DB that passed it. **0019 could never succeed on
  any real DB**, so no known DB ever got past 0017 (stage=0017,
  test=0017, CI never runs alembic — tests use `create_all`).
- **0023** re-`add_column`'d `file_name`/`file_size` already added by
  0021 (linear chain 0021→0022→0023) → would fail next.
- Latent since 2026-08-12/17; exposed 2026-10-16 by the TASK-0136 deploy
  fix (MR !56) — compose finally ran the freshly built image instead of a
  stale 2-month-old local one, so migrations actually re-ran.
- **Masking CI bug**: `deploy:*` health loop
  (`wget … && break || sleep 2`) fell through to "complete" after 30
  failed tries — deploy jobs reported success while the app was dead.

## Fix (red → green)

Red: `alembic upgrade head` on empty postgres:16 → DuplicateTable at 0019
(reproduced in throwaway container before the fix).

- 0019: `op.create_index(..., if_not_exists=True)` (FK part was already
  guarded with `DROP … IF EXISTS`).
- 0023: inspector-guarded — add missing columns only, widen existing
  `file_path` 512→1024 via `alter_column`.
- `deploy:dev` / `deploy:stage`: health loop now tracks success and
  `exit 1` + dumps `compose logs --tail 50 app` when never healthy.
- New CI job `backend:migrations` (test stage, postgres:16 service):
  `alembic upgrade head` on a fresh empty DB + `alembic current` — the
  regression test for the whole chain, on every MR/develop/main.

## AC

- [x] Red reproduced on empty DB (DuplicateTable at 0019)
- [x] Green: `0017 → 0023` upgrade passes (stage-path rehearsal)
- [x] Green: fresh empty DB full chain in one run → `0023 (head)`, 24 upgrades
- [x] CI lint `valid: true` with new `backend:migrations` job + fixed health checks
- [x] ruff check + format clean on changed migration files
- [x] Stage/dev recovery: verified after merge (see Evidence)

## Evidence

- Red: `alembic upgrade head` on empty DB → `DuplicateTable: relation
  "ix_task_feature_id" already exists`
- Green (0017→0023): log `Running upgrade 0018 → 0019 … 0022 → 0023`,
  `alembic current` → `0023`
- Green (from scratch): 24 × `Running upgrade`, `0023 (head)`
- CI lint: `{"valid": true, "errors": [], "warnings": []}`
- ruff: `All checks passed!`, `2 files already formatted`

## Out of scope / notes

- Test-env image (`upcp-test-app`, built 2026-08-07) has head=0017 — its
  own next restart will also exercise the fixed chain; watched separately.
- Bootstrap/migration history not rewritten (0019/0023 edited in place —
  safe: no DB ever recorded them as applied).
