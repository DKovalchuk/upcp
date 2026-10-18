"""Scenario: Database Restart During Active Requests

Tests that the app handles DB restart gracefully:
connection pool recovery, no data corruption, proper error handling.

Flow:
1. Verify healthy
2. Capture baseline
3. Restart PostgreSQL (not kill — graceful)
4. Monitor error rate during restart
5. Wait for full recovery
6. Verify data integrity
7. Compare resources
"""

from __future__ import annotations

import logging
import time

import httpx

from tests.chaos.assertions import (
    ChaosVerdict,
    assert_data_integrity,
    assert_error_rate,
    assert_http_available,
    assert_mttr,
    assert_resource_recovery,
    extract_count,
)
from tests.chaos.engine import ChaosEngine

logger = logging.getLogger("chaos.db_restart")


def run(
    engine: ChaosEngine,
    health_url: str = "http://localhost:38082/health",
    api_url: str = "http://localhost:38082/api/v1/projects",
    max_mttr_s: float = 45.0,
) -> ChaosVerdict:
    """Execute database restart experiment."""
    verdict = ChaosVerdict(experiment="db_restart")
    start_time = time.monotonic()

    logger.info("=== Database Restart Experiment ===")

    # 1. Verify healthy
    logger.info("Step 1: Verify system healthy")
    probe = engine.probe_http(health_url)
    if not probe["success"]:
        verdict.assertions.append(assert_http_available(health_url))
        verdict.passed = False
        return verdict

    # 2. Capture baseline
    try:
        baseline_mem = engine.get_resources("app").memory_mb
    except Exception:
        baseline_mem = 0.0

    try:
        resp = httpx.get(api_url, timeout=5, headers=engine.get_auth_headers())
        initial_count = extract_count(resp.json()) if resp.status_code == 200 else 0
    except Exception:
        initial_count = 0

    # 3. Restart DB (graceful, not kill)
    logger.info("Step 3: Restart PostgreSQL")
    t_restart = time.monotonic()
    engine.restart("db", timeout=10)

    # 4. Monitor error rate during restart
    logger.info("Step 4: Monitor error rate during recovery")
    total_requests = 0
    failed_requests = 0

    first_ok: float | None = None
    for _ in range(15):
        total_requests += 1
        try:
            resp = httpx.get(health_url, timeout=3)
            if resp.status_code >= 500:
                failed_requests += 1
            elif first_ok is None:
                first_ok = time.monotonic() - t_restart
        except Exception:
            failed_requests += 1
        time.sleep(1)

    verdict.assertions.append(
        assert_error_rate(total_requests, failed_requests, max_error_pct=50.0)
    )

    # 5. Wait for full recovery (readiness before integrity checks)
    logger.info("Step 5: Wait for full recovery")
    try:
        engine.wait_for_healthy("app", timeout=max_mttr_s)
    except TimeoutError:
        logger.warning("app not confirmed healthy within %ss before integrity checks", max_mttr_s)

    # MTTR = disruption start → first healthy response. The old flow
    # measured from AFTER the 15s monitor loop, so it always reported ~0.0s.
    verdict.mttr_seconds = first_ok if first_ok is not None else time.monotonic() - t_restart
    verdict.assertions.append(assert_mttr(verdict.mttr_seconds, max_mttr_s, "db_restart"))

    # 6. Verify data integrity
    logger.info("Step 6: Verify data integrity")
    verdict.assertions.append(
        assert_data_integrity(api_url, initial_count, headers=engine.get_auth_headers())
    )

    # 7. Resource comparison
    logger.info("Step 7: Resource comparison")
    try:
        after_mem = engine.get_resources("app").memory_mb
        verdict.assertions.append(assert_resource_recovery(baseline_mem, after_mem))
    except Exception as e:
        logger.warning("Resource check failed: %s", e)

    verdict.duration_seconds = time.monotonic() - start_time
    verdict.passed = all(a.passed for a in verdict.assertions)

    logger.info(verdict.summary)
    return verdict
