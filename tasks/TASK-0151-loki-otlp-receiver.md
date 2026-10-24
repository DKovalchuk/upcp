# TASK-0151 — Loki OTLP receiver (SPEC-0024 follow-up, TASK-0140 finding)

**Spec:** SPEC-0024 observability follow-up — finding: collector→loki:4317 refused; top-level `otlp:` invalid in loki 3.4.2 (reverted to "healthy" with the export path still dead)
**Milestone:** Этап 1 perf-расследования
**Points:** 3
**Status:** DONE (closed 2026-10-24)

## Investigation (2026-10-24, all empirical on grafana/loki:3.4.2)

1. **Reproduced**: collector logs spammed `dial tcp 172.21.0.2:4317:
   connection refused` + `Exporting failed. Will retry` (otlp/loki, logs
   pipeline); probe POST to collector `/v1/logs` → 200 `partialSuccess`
   accepted, export never landed (loki query empty).
2. **Receiver location found**:
   - `-verify-config` with top-level `otlp:` (+variants) →
     `field otlp not found in type loki.ConfigWrapper` — finding
     reproduced; binary yaml tags confirm only `otlp_config`
     (attribute-mapping under limits) exists;
   - running container port probe: **3100 OPEN, 4317/4318 CLOSED**;
   - `POST /otlp/v1/logs` on the main HTTP port → **400 with a real Loki
     ingest error** (`entry ... has timestamp too old`) — i.e. the path
     parses and ingests; `/v1/logs` → 404.
   → Native OTLP = **HTTP on the main port under `/otlp`** (no separate
   gRPC listener in this build).

## Objective

Point the collector's logs pipeline at the working receiver
(OTLP/HTTP → `http://loki:3100/otlp`) and pin both configs with
contract tests so neither the dead gRPC endpoint nor the invalid
`otlp:` block can return.

## Acceptance Criteria (verified 2026-10-24)

- [x] **Red first:** `test_observability_configs.py` red (collector
      contract) → **green 2/2** after the fix (assertion distinguishes
      exporter *directives* from historical comments)
- [x] Collector config: `otlphttp/loki` exporter, endpoint
      `http://loki:3100/otlp`, logs pipeline references it; no
      `endpoint: loki:4317` directive
- [x] loki-config guard: no top-level `otlp:` key (fails -verify-config
      on 3.4.2)
- [x] Live end-to-end (compose up → probe → query → down): after
      collector restart **0 refused-errors**; probe accepted
      (HTTP 200 at :4320/v1/logs) and **queryable in Loki**
      (`{service_name="loki-otlp-probe"}` → 1 stream / 1 entry —
      label from Loki's default `service.name` index-labels)
- [x] Full backend suite green (**996 passed**, 3 pre-existing
      `test_redis`); ruff/format clean; mypy 114 files; both YAMLs
      `safe_load` ✓
- [x] Stack torn down; extracted binary cleaned

## Evidence

- Red→green: `1 failed / 1 passed` → `2 passed`
- Live: collector before fix = permanent refused-retry; after fix =
  0 loki errors (only tempo DNS warnings — tempo service not started
  during the probe; full observability profile starts it — out of scope)
- LogQL `query_range{service_name="loki-otlp-probe"}` → streams 1,
  entries 1

## Notes

1. Contract-test assertion scoped to `endpoint: loki:4317` (directives)
   rather than the bare substring — the evidence comment in the config
   legitimately mentions the dead endpoint.
2. OTLP receiver needs **no loki-config change at all** (mounted by
   default on the main HTTP server) — the fix is purely export-side.

## Files

| File | Action |
|------|--------|
| `observability/otel-collector-config.yaml` | MODIFY — `otlphttp/loki` → `http://loki:3100/otlp`; logs pipeline |
| `backend/tests/test_observability_configs.py` | CREATE (red→green, 2 contract tests) |
