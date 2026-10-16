# Performance Testing — UPCP Test Environment

## Quick Start

```bash
# Start test environment
docker compose -f docker-compose.test.yml up -d

# Seed test data
docker compose -f docker-compose.test.yml run --rm --profile tools seeder

# Run smoke test (10 users, 30s)
python tests/performance/runner.py --profile smoke

# Run load test with report
python tests/performance/runner.py --profile load --report --save-baseline

# Run specific scenario
python tests/performance/runner.py --scenario scenario_concurrency --users 50 --run-time 3m

# Open Locust Web UI
docker compose -f docker-compose.test.yml --profile perf up -d locust-master
# → http://localhost:38089
```

## Profiles

| Profile | Users | Duration | Purpose |
|---------|-------|----------|---------|
| smoke | 10 | 30s | Quick sanity check |
| load | 50 | 5m | Normal operational load |
| stress | 200 | 10m | Peak load testing |
| soak | 50 | 30m | Endurance / memory leak detection |
| spike | 500 | 3m | Sudden traffic spike |
| projects | 50 | 5m | Project CRUD focused |
| tasks | 50 | 5m | Task workflow focused |
| dashboard | 100 | 5m | Read-heavy analytics |
| agents | 30 | 5m | Agent workflow focused |
| concurrency | 50 | 3m | Race condition / contention |
| all | 30 | 3m×7 | Sequential all scenarios |

## Scenarios

| Scenario | File | Focus |
|----------|------|-------|
| Mixed Workload | scenario_mixed.py | Realistic usage across all endpoints |
| Project CRUD | scenario_projects.py | Project + structure operations |
| Task Workflow | scenario_tasks.py | Delivery lifecycle (create→claim→done) |
| Dashboard | scenario_dashboard.py | Stats, attention, portfolio, analytics |
| Agent Ops | scenario_agents.py | Self-service + claims + heartbeats |
| Search | scenario_search.py | Global search + pagination |
| Concurrency | scenario_concurrency.py | Race conditions, rate limits, contention |

## SLI/SLO

Defined in `config/sli_slo.yaml`. Key targets:

- **Availability:** 99.9% (non-5xx responses)
- **P95 Latency:** < 1 second
- **P99 Latency:** < 2 seconds
- **Throughput:** > 50 req/s under normal load
- **Error Rate:** < 1%

## Analyzer

```bash
# Check SLO compliance
python tests/performance/analyzer.py --input results/ --check-slo

# Compare with baseline
python tests/performance/analyzer.py --input results/ --compare-baseline

# Generate report
python tests/performance/analyzer.py --input results/ --generate-report --output reports/report.md

# Update trend history
python tests/performance/analyzer.py --input results/ --save-baseline
```

## Grafana Dashboards

Access: http://localhost:33001 (admin/admin_test)

- **UPCP Test — Overview:** Request rate, latency, errors, DB pool
- **UPCP Test — Performance:** Detailed latency by handler, auth attempts, rate limits
- **UPCP Test — Resources:** Memory, CPU, GC, FDs, Redis ops

## Architecture

```
runner.py → Locust CLI → scenario_*.py → HTTP → test environment
                ↓
         results/*.csv
                ↓
analyzer.py → reports/*.md + baseline.json + trend_history.json
```

## Files

```
tests/performance/
├── locustfiles/
│   ├── __init__.py
│   ├── common.py              # UPCPBaseUser (auth, health check, helpers)
│   ├── scenario_mixed.py      # Mixed realistic workload
│   ├── scenario_projects.py   # Project CRUD
│   ├── scenario_tasks.py      # Task workflow
│   ├── scenario_dashboard.py  # Dashboard & analytics
│   ├── scenario_agents.py     # Agent operations
│   ├── scenario_search.py     # Search & pagination
│   └── scenario_concurrency.py # Race conditions & contention
├── config/
│   ├── profiles.yaml          # Load profiles (users, duration, SLOs)
│   └── sli_slo.yaml           # SLI/SLO definitions + regression thresholds
├── results/                   # JSON/CSV results (gitignored except baseline)
├── reports/                   # Generated markdown reports
├── analyzer.py                # Results analysis + trend tracking
├── runner.py                  # Orchestration + pre-test validation
├── .gitignore
└── README.md                  # This file
```
