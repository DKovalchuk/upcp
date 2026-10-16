# Chaos Engineering — UPCP Test Environment

## Quick Start

```bash
# Start test environment
docker compose -f docker-compose.test.yml up -d

# Seed test data
docker compose -f docker-compose.test.yml run --rm --profile tools seeder

# Run quick chaos suite (3 experiments, ~3 min)
python tests/chaos/runner.py --profile quick --report

# Run full chaos suite (7 experiments, ~15 min)
python tests/chaos/runner.py --profile full --report

# Run single experiment
python tests/chaos/runner.py --experiment service_kill_app

# List available experiments
python tests/chaos/runner.py --list
```

## Experiments

| Experiment | Description | Max MTTR |
|------------|-------------|----------|
| `service_kill_app` | Kill app container (SIGKILL) | 30s |
| `service_kill_db` | Kill DB container (SIGKILL) | 45s |
| `redis_failure` | Stop Redis → graceful degradation → recovery | 30s |
| `cascade_redis_app` | Redis failure → app degradation → recovery chain | 60s |
| `db_restart` | Restart PostgreSQL during active requests | 45s |
| `app_restart` | Kill app mid-request, verify clean restart | 30s |
| `full_outage` | Kill all services, restart in order (DB→Redis→App) | 90s |

## Profiles

| Profile | Experiments | Duration | Purpose |
|---------|-------------|----------|---------|
| quick | 3 | ~3 min | Smoke test — basic resilience |
| standard | 5 | ~8 min | Standard validation |
| full | 7 | ~15 min | Comprehensive chaos testing |
| resilience | 3 | ~10 min | Focus on cascade/outage scenarios |

## Assertions

Each experiment validates:

- **MTTR** — Mean Time To Recovery within threshold
- **Detection** — Fault detection time within threshold
- **Data Integrity** — No data loss after chaos
- **Graceful Degradation** — Core functionality works when dependencies fail
- **Error Rate** — Error rate during chaos within tolerance
- **Resource Recovery** — Memory returns to baseline (no leaks)

## Architecture

```
runner.py → engine.py → Docker API → test containers
    ↓              ↓
scenarios/     assertions.py
    ↓              ↓
results/*.json  reports/*.md
```

## Files

```
tests/chaos/
├── __init__.py
├── engine.py              # Docker-based fault injection engine
├── assertions.py          # MTTR, data integrity, degradation checks
├── runner.py              # Orchestration + reporting
├── config/
│   └── chaos_profiles.yaml  # Experiment + profile definitions
├── scenarios/
│   ├── __init__.py
│   ├── service_kill.py    # Kill + recovery
│   ├── redis_failure.py   # Redis down → degradation
│   ├── cascade_failure.py # Redis → App cascade
│   ├── db_restart.py      # DB restart during traffic
│   ├── app_restart.py     # App kill during traffic
│   └── full_outage.py     # Total outage + ordered recovery
├── results/               # JSON results (gitignored)
├── reports/               # Markdown reports
├── .gitignore
└── README.md              # This file
```

## Grafana Dashboard

Access: http://localhost:33001 → **UPCP Test — Chaos Engineering**

Shows: error rate, latency p95/p99, DB pool, memory, rate limit hits during chaos experiments.

## Dependencies

- Docker Python SDK: `pip install docker`
- httpx: `pip install httpx`
