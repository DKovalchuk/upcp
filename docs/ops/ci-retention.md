# CI & Registry Retention (TASK-0136)

Disk growth on the shared runner host (images, volumes, registry tags) is
bounded by three rules, added 2026-10-16 (variant A: retention only — build
process unchanged).

## 1. Registry expiration policy — automatic, daily

Project → Settings → Container registry (applied via API):

| Setting | Value | Why |
|---|---|---|
| `cadence` | `1d` | daily sweep |
| `keep_n` | `10` | keep the last 10 SHA tags per repository |
| `older_than` | `null` | tag `created_at` is unavailable for OCI-index manifests (third-party cleanup path — registry metadata API `/gitlab/v1/` is not exposed), so an age filter would block *every* deletion; `keep_n` alone bounds growth |
| `name_regex` | `[0-9a-f]{7,40}` | only CI SHA tags are deletion candidates |
| `name_regex_keep` | `(dev\|stage\|latest)` | floating tags are never deleted |

**Known limitation:** with `created_at` unavailable, "which 10 SHA tags
survive" is not date-ordered. The latest build is always reachable under
`:dev`, and any older commit can be rebuilt from git.

## 2. Every build cleans up after itself

`build:backend` / `build:frontend` `after_script`:

- removes local tags except the branch's floating tag (already pushed to
  the registry): `:dev` on develop, `:stage` on main — that tag is kept as
  the `--cache-from` source for the next build of the same branch;
- `docker image prune -f --filter until=24h` — untagged images older than
  24h; docker never removes images referenced by any container (verified
  against moby prune source), so other projects' containers are safe — only
  untagged, unreferenced build leftovers are swept.

Builds cache from the branch floating tag first, plus `:dev` as a
cross-branch fallback (BuildKit ignores a `--cache-from` image that does
not exist in the registry). The registry `name_regex_keep=(dev|stage|latest)`
policy covers both floating tags.

## 3. Manual sweep — `maintenance:cleanup` job

Run from the pipeline page (develop/main, `when: manual`, `allow_failure`):

1. removes local SHA tags of both upcp repos;
2. removes dangling images older than 30 days;
3. removes `runner-*-cache-*` volumes older than 30 days with no linked
   container — worst case the next build re-warms its cache.

`resource_group: maintenance` prevents concurrent runs.

## Garbage collection

The registry runs with the **metadata database**, so **online GC is
automatic** (continuous, zero-downtime — GitLab docs: *"run garbage collection
in the background without the need to schedule it or require read-only
mode"*). `gitlab-ctl registry-garbage-collect` does **not** run in this mode
(*"This command does not proceed if the container registry metadata database
is enabled"* — confirmed by attempting a dry-run). Blobs of deleted tags are
reclaimed automatically (default review window `24h`).

## One-time cleanup executed 2026-10-16

- Registry tags: backend `81 → 11`, frontend `58 → 11` (oldest SHA tags
  deleted, ordered by git commit date; `dev` kept);
- Runner cache volumes: 44 orphaned `runner-*-cache-*` removed,
  `18.84 GB → 11.43 GB` (150 → 106 volumes);
- Local stale SHA tags + dead `upcp-backend:stage` / `upcp-frontend:stage`
  aliases removed;
- Images referenced by (stopped) containers were skipped by design; other
  projects on this shared host were not touched.
