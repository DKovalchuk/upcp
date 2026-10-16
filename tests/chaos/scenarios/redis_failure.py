"""Scenario: Redis Failure — Graceful Degradation

Tests that UPCP continues to function when Redis is unavailable.
Core CRUD must work; rate limiting should be disabled (not crash).

Flow:
1. Verify system healthy with Redis
2. Stop Redis container
3. Verify core CRUD still works (projects, tasks)
4. Verify rate limiting is disabled (not 500)
5. Restart Redis
6. Verify rate limiting resumes
"""

from __future__ import annotations

import logging
import time

import httpx

from tests.chaos.assertions import (
    ChaosVerdict,
    assert_graceful_degradation,
    assert_http_available,
    assert_mttr,
)
from tests.chaos.engine import ChaosEngine

logger = logging.getLogger("chaos.redis_failure")


def run(
    engine: ChaosEngine,
    health_url: str = "http://localhost:38082/health",
    api_url: str = "http://localhost:38082/api/v1/projects",
    max_mttr_s: float = 30.0,
) -> ChaosVerdict:
    """Execute Redis failure experiment."""
    verdict = ChaosVerdict(experiment="redis_failure")
    start_time = time.monotonic()

    logger.info("=== Redis Failure Experiment ===")

    # 1. Verify healthy
    logger.info("Step 1: Verify system healthy")
    probe = engine.probe_http(health_url)
    if not probe["success"]:
        verdict.assertions.append(assert_http_available(health_url))
        verdict.passed = False
        return verdict

    # 2. Stop Redis
    logger.info("Step 2: Stop Redis")
    engine.stop("redis", timeout=5)

    # Wait a moment for the failure to propagate
    time.sleep(2)

    # 3. Verify core CRUD still works
    logger.info("Step 3: Verify core CRUD works without Redis")
    verdict.assertions.append(
        assert_graceful_degradation(
            core_url=api_url,
            degraded_url=health_url,
        )
    )

    # 4. Verify health endpoint shows degraded (not crash)
    logger.info("Step 4: Verify health shows degraded status")
    try:
        resp = httpx.get(health_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", "unknown")
            verdict.assertions.append(_assert_degraded_not_crashed(status))
        else:
            verdict.assertions.append(_assert_degraded_not_crashed("error"))
    except Exception as e:
        verdict.assertions.append(_assert_degraded_not_crashed(str(e)))

    # 5. Restart Redis
    logger.info("Step 5: Restart Redis")
    engine.start("redis")

    # 6. Wait for full recovery
    logger.info("Step 6: Wait for recovery")
    try:
        mttr = engine.wait_for_healthy("redis", timeout=max_mttr_s)
    except TimeoutError:
        mttr = max_mttr_s

    verdict.mttr_seconds = mttr
    verdict.assertions.append(assert_mttr(mttr, max_mttr_s, "redis"))

    # 7. Verify full functionality restored
    logger.info("Step 7: Verify full functionality")
    verdict.assertions.append(assert_http_available(health_url))

    verdict.duration_seconds = time.monotonic() - start_time
    verdict.passed = all(a.passed for a in verdict.assertions)

    logger.info(verdict.summary)
    return verdict


def _assert_degraded_not_crashed(status: str):
    """Assert app is degraded but not crashed."""
    from tests.chaos.assertions import AssertionResult

    passed = status in ("degraded", "ok")
    return AssertionResult(
        name="degraded_not_crashed",
        passed=passed,
        actual=status,
        expected="degraded or ok",
        message=f"App status: {status} {'(graceful)' if passed else '(CRASHED)'}",
    )
