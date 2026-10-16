"""Scenario: Cascade Failure — Redis down → App behavior → Recovery chain

Tests cascading failure resilience:
1. Redis fails → App degrades gracefully
2. App continues serving core CRUD
3. Redis recovers → App fully recovers
4. No data loss throughout

This is the most important chaos scenario for UPCP because
Redis is used for rate limiting — its failure must not crash the app.
"""

from __future__ import annotations

import logging
import time

import httpx

from tests.chaos.assertions import (
    ChaosVerdict,
    assert_data_integrity,
    assert_error_rate,
    assert_graceful_degradation,
    assert_http_available,
    assert_mttr,
    assert_resource_recovery,
)
from tests.chaos.engine import ChaosEngine

logger = logging.getLogger("chaos.cascade_failure")


def run(
    engine: ChaosEngine,
    health_url: str = "http://localhost:38082/health",
    api_url: str = "http://localhost:38082/api/v1/projects",
    max_mttr_s: float = 60.0,
) -> ChaosVerdict:
    """Execute cascade failure experiment."""
    verdict = ChaosVerdict(experiment="cascade_redis_app")
    start_time = time.monotonic()

    logger.info("=== Cascade Failure Experiment: Redis → App ===")

    # Phase 1: Baseline
    logger.info("Phase 1: Baseline")
    probe = engine.probe_http(health_url)
    if not probe["success"]:
        verdict.assertions.append(assert_http_available(health_url))
        verdict.passed = False
        return verdict

    try:
        baseline_mem = engine.get_resources("app").memory_mb
    except Exception:
        baseline_mem = 0.0

    # Count existing data
    try:
        resp = httpx.get(api_url, timeout=5)
        initial_count = len(resp.json()) if resp.status_code == 200 else 0
    except Exception:
        initial_count = 0

    # Phase 2: Inject failure (stop Redis)
    logger.info("Phase 2: Stop Redis")
    engine.stop("redis", timeout=5)
    time.sleep(3)  # Let failure propagate

    # Phase 3: Verify degradation
    logger.info("Phase 3: Verify graceful degradation")
    total_requests = 0
    failed_requests = 0

    # Probe API multiple times during degradation
    for _ in range(10):
        total_requests += 1
        try:
            resp = httpx.get(api_url, timeout=5)
            if resp.status_code >= 500:
                failed_requests += 1
        except Exception:
            failed_requests += 1
        time.sleep(0.5)

    verdict.assertions.append(
        assert_error_rate(total_requests, failed_requests, max_error_pct=30.0)
    )

    # Verify core still responds
    verdict.assertions.append(
        assert_graceful_degradation(
            core_url=api_url,
            degraded_url=health_url,
        )
    )

    # Phase 4: Recover Redis
    logger.info("Phase 4: Restart Redis")
    engine.start("redis")

    try:
        mttr = engine.wait_for_healthy("redis", timeout=max_mttr_s)
    except TimeoutError:
        mttr = max_mttr_s

    verdict.mttr_seconds = mttr
    verdict.assertions.append(assert_mttr(mttr, max_mttr_s, "redis_cascade"))

    # Phase 5: Verify full recovery
    logger.info("Phase 5: Verify full recovery")
    time.sleep(2)  # Let app reconnect

    verdict.assertions.append(assert_http_available(health_url))

    verdict.assertions.append(assert_data_integrity(api_url, initial_count))

    # Phase 6: Resource comparison
    logger.info("Phase 6: Resource comparison")
    try:
        after_mem = engine.get_resources("app").memory_mb
        verdict.assertions.append(assert_resource_recovery(baseline_mem, after_mem))
    except Exception as e:
        logger.warning("Resource check failed: %s", e)

    verdict.duration_seconds = time.monotonic() - start_time
    verdict.passed = all(a.passed for a in verdict.assertions)

    logger.info(verdict.summary)
    return verdict
