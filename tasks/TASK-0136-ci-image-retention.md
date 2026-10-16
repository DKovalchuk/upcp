# TASK-0136 — CI Image & Cache Retention

**Milestone:** ops/CI
**Points:** 3
**Spec:** mini-spec (this file), user decision 2026-10-16: variant A "retention"
**Status:** DONE

## Context

CI builds on the shared laptop runner accumulate disk:
registry SHA tags grow forever (81 backend / 58 frontend tags), local docker
images keep every built SHA tag, runner cache volumes are never GC'd
(orphaned `runner-*-cache-*` volumes). GitLab expiration policy existed but
`enabled: false` since 2026-07.

User explicitly chose: **retention rules + delete old** — NOT process
restructure. Dev environment docker flows are not to be touched.

## Key diagnostic findings

- Registry has **no** `/gitlab/v1/` metadata API (`supports_gitlab_api?` →
  false; Faraday `GET /gitlab/v1/` → 404) → cleanup runs third-party path.
- Tags are OCI image **indexes** (BuildKit provenance attestation) →
  `manifest['config']` missing → `created_at` = nil for every tag →
  `older_than` age filter can never match → policy deleted 0 tags while it
  was set. **Fix: `older_than: null`, rely on `keep_n=10` only.**
- Offline `registry-garbage-collect` refuses to run with database metadata
  ("does not proceed if metadata database is enabled") → **online GC is
  automatic** (GitLab docs), blobs of deleted tags reclaimed automatically.
- `docker image prune` (no `-a`) skips images referenced by running OR
  stopped containers (verified in moby source) → safe on shared host.

## AC

- [x] Container expiration policy enabled: SHA-only regex `[0-9a-f]{7,40}`,
      keep_n=10, older_than=null (age filter unusable — see findings),
      name_regex_keep protects dev/stage/latest
- [x] One-time policy cleanup triggered → tag counts drop:
      backend 81→11, frontend 58→11, verified via API X-Total
- [x] Registry GC dry-run attempted → refused with database-metadata message;
      online GC confirmed automatic (docs) — no manual GC needed;
      registry size measured 469MB
- [x] `.gitlab-ci.yml` build jobs: after_script drops local SHA tags after
      push, prunes dangling images `until=24h` (CI lint valid: true)
- [x] Manual `maintenance:cleanup` job: stale SHA tags, dangling >30d,
      runner cache volumes >30d (volume rm refuses in-use → safe);
      `resource_group: maintenance`; CI lint valid: true
- [x] One-time cleanup executed: local stale SHA tags (4) + dead
      `upcp-*:stage` aliases removed (2 images, ~700MB); 44 orphaned runner
      cache volumes removed → local volumes 18.84GB → 11.43GB;
      dangling >30d prune = 0B (all 5 dangling images are referenced by
      stopped containers — skipped by design); other projects untouched
- [x] Docs: `docs/ops/ci-retention.md` created + INDEX updated
- [x] PROJECT_STATUS updated

## Out of scope (known findings, need separate decision)

- **Deploy tag mismatch**: CI does `docker tag $REGISTRY/...:dev upcp-backend:stage`,
  but `docker-compose.stage.yml` references
  `registry.gitlab.local/.../backend:stage` (no `:5050`) — compose uses a
  stale local image; deploy may not actually update app code. Requires CD
  rework (variant B/C) — flagged, not fixed here.
- Tag collision `:dev` pushed from both develop and main.

## Evidence

- API policy GET: `enabled=true, keep_n=10, older_than=null,
  name_regex=[0-9a-f]{7,40}, name_regex_keep=(dev|stage|latest)`
- Tag counts after cleanup: 11 / 11 (X-Total)
- CI lint: `valid: true` (both edits)
- `docker system df`: volumes 150→106, 18.84GB→11.43GB
- Registry GC: `registry-garbage-collect -d` → "not compatible with
  database metadata, please use online garbage collection instead"
