"""Scenario: Service Kill + Recovery

Tests system resilience when a critical service is killed unexpectedly.
Measures detection time and MTTR (Mean Time To Recovery).

Flow:
1. Verify system healthy
2. Capture baseline resources
3. Kill target service (SIGKILL)
4. Measure detection time (health check failure)
5. Restart service
6. Measure recovery time (health check success)
7. Verify data integrity
8. Compare resources before/after
"""

from __future__ import annotations

import logging
import time

from tests.chaos.assertions import (
    ChaosVerdict,
    assert_data_integrity,
    assert_detection,
    assert_http_available,
    assert_mttr,
    assert_resource_recovery,
)
from tests.chaos.engine import ChaosEngine

logger = logging.getLogger("chaos.service_kill")


def run(
    engine: ChaosEngine,
    service: str = "app",
    health_url: str = "http://localhost:38082/health",
    data_url: str = "http://localhost:38082/api/v1/projects",
    expected_data_count: int = 1,
    max_detection_s: float = 15.0,
    max_mttr_s: float = 30.0,
) -> ChaosVerdict:
    """Execute service kill experiment."""
    verdict = ChaosVerdict(experiment=f"service_kill_{service}")
    start_time = time.monotonic()

    logger.info("=== Service Kill Experiment: %s ===", service)

    # 1. Verify healthy
    logger.info("Step 1: Verify system healthy")
    probe = engine.probe_http(health_url)
    if not probe["success"]:
        verdict.assertions.append(assert_http_available(health_url))
        verdict.passed = False
        return verdict

    # 2. Capture baseline resources
    logger.info("Step 2: Capture baseline resources")
    try:
        baseline_mem = engine.get_resources(service).memory_mb
    except Exception:
        baseline_mem = 0.0

    # 3. Kill service
    logger.info("Step 3: Kill %s", service)
    engine.kill(service)

    # 4. Measure detection time
    logger.info("Step 4: Measure detection time")
    try:
        detection_time = engine.wait_for_unhealthy(service, timeout=max_detection_s)
    except TimeoutError:
        detection_time = max_detection_s

    verdict.detection_seconds = detection_time
    verdict.assertions.append(assert_detection(detection_time, max_detection_s, service))

    # 5. Restart
    logger.info("Step 5: Restart %s", service)
    engine.start(service)

    # 6. Measure recovery
    logger.info("Step 6: Wait for recovery")
    try:
        mttr = engine.wait_for_healthy(service, timeout=max_mttr_s)
    except TimeoutError:
        mttr = max_mttr_s

    verdict.mttr_seconds = mttr
    verdict.assertions.append(assert_mttr(mttr, max_mttr_s, service))

    # 7. Verify data integrity
    logger.info("Step 7: Verify data integrity")
    verdict.assertions.append(assert_data_integrity(data_url, expected_data_count))

    # 8. Resource comparison
    logger.info("Step 8: Compare resources")
    try:
        after_mem = engine.get_resources(service).memory_mb
        verdict.assertions.append(assert_resource_recovery(baseline_mem, after_mem))
    except Exception as e:
        logger.warning("Resource check failed: %s", e)

    verdict.duration_seconds = time.monotonic() - start_time
    verdict.passed = all(a.passed for a in verdict.assertions)

    logger.info(verdict.summary)
    return verdict
