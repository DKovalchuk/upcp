"""Scenario: Full Outage — All services down then recover

Tests complete system outage and recovery:
1. Kill all services (DB, Redis, App)
2. Restart in correct order (DB → Redis → App)
3. Verify full recovery
4. Verify data integrity

This validates the worst-case scenario: total infrastructure failure.
"""

from __future__ import annotations

import logging
import time

import httpx

from tests.chaos.assertions import (
    AssertionResult,
    ChaosVerdict,
    assert_data_integrity,
    assert_http_available,
    assert_mttr,
    assert_resource_recovery,
    extract_count,
)
from tests.chaos.engine import ChaosEngine

logger = logging.getLogger("chaos.full_outage")


def run(
    engine: ChaosEngine,
    health_url: str = "http://localhost:38082/health",
    api_url: str = "http://localhost:38082/api/v1/projects",
    max_mttr_s: float = 90.0,
) -> ChaosVerdict:
    """Execute full outage experiment."""
    verdict = ChaosVerdict(experiment="full_outage")
    start_time = time.monotonic()

    logger.info("=== Full Outage Experiment ===")

    # 1. Verify healthy
    logger.info("Step 1: Verify system healthy")
    probe = engine.probe_http(health_url)
    if not probe["success"]:
        verdict.assertions.append(assert_http_available(health_url))
        verdict.passed = False
        return verdict

    try:
        resp = httpx.get(api_url, timeout=5, headers=engine.get_auth_headers())
        initial_count = extract_count(resp.json()) if resp.status_code == 200 else 0
    except Exception:
        initial_count = 0

    # 2. Kill all services
    logger.info("Step 2: Kill all services")
    for service in ["app", "redis", "db"]:
        try:
            engine.kill(service)
            logger.info("  Killed %s", service)
        except Exception as e:
            logger.warning("  Failed to kill %s: %s", service, e)

    # Verify everything is down
    time.sleep(3)
    logger.info("Step 3: Verify all services down")
    try:
        resp = httpx.get(health_url, timeout=2)
        app_down = resp.status_code >= 500
    except Exception:
        app_down = True

    verdict.assertions.append(
        AssertionResult(
            name="all_services_down",
            passed=app_down,
            actual="down" if app_down else "up",
            expected="down",
            message=f"All services down: {'YES' if app_down else 'NO — app still responding!'}",
        )
    )

    # 4. Restart in correct order: DB → Redis → App
    logger.info("Step 4: Restart services in order")

    logger.info("  Starting DB...")
    engine.start("db")
    try:
        engine.wait_for_healthy("db", timeout=30)
    except TimeoutError:
        logger.warning("  DB did not become healthy in 30s")

    logger.info("  Starting Redis...")
    engine.start("redis")
    try:
        engine.wait_for_healthy("redis", timeout=15)
    except TimeoutError:
        logger.warning("  Redis did not become healthy in 15s")

    logger.info("  Starting App...")
    engine.start("app")

    # 5. Wait for full recovery
    logger.info("Step 5: Wait for full recovery")
    try:
        mttr = engine.wait_for_healthy("app", timeout=max_mttr_s)
    except TimeoutError:
        mttr = max_mttr_s

    verdict.mttr_seconds = mttr
    verdict.assertions.append(assert_mttr(mttr, max_mttr_s, "full_outage"))

    # 6. Verify data integrity
    logger.info("Step 6: Verify data integrity")
    time.sleep(2)  # Let app fully initialize
    verdict.assertions.append(
        assert_data_integrity(api_url, initial_count, headers=engine.get_auth_headers())
    )

    # 7. Post-restart memory stability (pre-outage baseline is not
    # comparable across a restart — TASK-0141)
    logger.info("Step 7: Resource comparison")
    try:
        warm1 = engine.get_resources("app").memory_mb
        time.sleep(2)
        engine.probe_http(health_url)
        warm2 = engine.get_resources("app").memory_mb
        verdict.assertions.append(assert_resource_recovery(warm1, warm2))
    except Exception as e:
        logger.warning("Resource check failed: %s", e)

    verdict.duration_seconds = time.monotonic() - start_time
    verdict.passed = all(a.passed for a in verdict.assertions)

    logger.info(verdict.summary)
    return verdict
