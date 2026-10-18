"""Scenario: App Restart During Active Requests

Tests that in-flight requests are handled gracefully during app restart.
No data corruption, clean restart, connection pool recovery.

Flow:
1. Verify healthy
2. Start background HTTP traffic
3. Kill app mid-request
4. Restart app
5. Verify recovery
6. Verify data integrity
"""

from __future__ import annotations

import logging
import threading
import time

import httpx

from tests.chaos.assertions import (
    ChaosVerdict,
    assert_data_integrity,
    assert_error_rate,
    assert_http_available,
    assert_mttr,
    extract_count,
)
from tests.chaos.engine import ChaosEngine

logger = logging.getLogger("chaos.app_restart")


def _background_traffic(url: str, duration_s: float, results: list[bool]) -> None:
    """Generate background HTTP traffic."""
    end_time = time.monotonic() + duration_s
    while time.monotonic() < end_time:
        try:
            resp = httpx.get(url, timeout=2)
            results.append(resp.status_code < 500)
        except Exception:
            results.append(False)
        time.sleep(0.2)


def run(
    engine: ChaosEngine,
    health_url: str = "http://localhost:38082/health",
    api_url: str = "http://localhost:38082/api/v1/projects",
    max_mttr_s: float = 30.0,
) -> ChaosVerdict:
    """Execute app restart during active traffic experiment."""
    verdict = ChaosVerdict(experiment="app_restart_during_traffic")
    start_time = time.monotonic()

    logger.info("=== App Restart During Traffic Experiment ===")

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

    # 2. Start background traffic
    logger.info("Step 2: Start background traffic")
    traffic_results: list[bool] = []
    traffic_thread = threading.Thread(
        target=_background_traffic,
        args=(api_url, 15.0, traffic_results),
        daemon=True,
    )
    traffic_thread.start()

    # Let traffic run for 2 seconds before disruption
    time.sleep(2)

    # 3. Kill app mid-request
    logger.info("Step 3: Kill app")
    engine.kill("app")

    # 4. Restart app
    logger.info("Step 4: Restart app")
    time.sleep(1)
    engine.start("app")

    # 5. Wait for recovery
    logger.info("Step 5: Wait for recovery")
    try:
        mttr = engine.wait_for_healthy("app", timeout=max_mttr_s)
    except TimeoutError:
        mttr = max_mttr_s

    verdict.mttr_seconds = mttr
    verdict.assertions.append(assert_mttr(mttr, max_mttr_s, "app_restart"))

    # Wait for traffic thread to finish
    traffic_thread.join(timeout=20)

    # 6. Check error rate during chaos
    logger.info("Step 6: Check error rate")
    if traffic_results:
        failed = sum(1 for r in traffic_results if not r)
        verdict.assertions.append(
            assert_error_rate(len(traffic_results), failed, max_error_pct=60.0)
        )

    # 7. Verify data integrity
    logger.info("Step 7: Verify data integrity")
    verdict.assertions.append(
        assert_data_integrity(api_url, initial_count, headers=engine.get_auth_headers())
    )

    verdict.duration_seconds = time.monotonic() - start_time
    verdict.passed = all(a.passed for a in verdict.assertions)

    logger.info(verdict.summary)
    return verdict
