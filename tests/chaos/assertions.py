"""Chaos assertions — validate system behavior during and after fault injection.

Checks: MTTR, data integrity, graceful degradation, error rate, resource recovery.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger("chaos.assertions")


@dataclass
class AssertionResult:
    name: str
    passed: bool
    actual: object = None
    expected: object = None
    message: str = ""


@dataclass
class ChaosVerdict:
    experiment: str
    passed: bool
    assertions: list[AssertionResult] = field(default_factory=list)
    mttr_seconds: float = 0.0
    detection_seconds: float = 0.0
    duration_seconds: float = 0.0

    @property
    def summary(self) -> str:
        passed = sum(1 for a in self.assertions if a.passed)
        total = len(self.assertions)
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.experiment}: {passed}/{total} assertions passed, MTTR={self.mttr_seconds:.1f}s"


def assert_mttr(actual_seconds: float, max_seconds: float, service: str) -> AssertionResult:
    """Assert Mean Time To Recovery is within threshold."""
    passed = actual_seconds <= max_seconds
    return AssertionResult(
        name=f"mttr_{service}",
        passed=passed,
        actual=round(actual_seconds, 2),
        expected=max_seconds,
        message=f"MTTR {service}: {actual_seconds:.1f}s {'<=' if passed else '>'} {max_seconds}s",
    )


def assert_detection(actual_seconds: float, max_seconds: float, service: str) -> AssertionResult:
    """Assert fault detection time is within threshold."""
    passed = actual_seconds <= max_seconds
    return AssertionResult(
        name=f"detection_{service}",
        passed=passed,
        actual=round(actual_seconds, 2),
        expected=max_seconds,
        message=f"Detection {service}: {actual_seconds:.1f}s {'<=' if passed else '>'} {max_seconds}s",
    )


def assert_http_available(url: str, timeout: float = 5.0) -> AssertionResult:
    """Assert HTTP endpoint responds with non-5xx."""
    try:
        resp = httpx.get(url, timeout=timeout)
        passed = resp.status_code < 500
        return AssertionResult(
            name="http_available",
            passed=passed,
            actual=resp.status_code,
            expected="< 500",
            message=f"HTTP {url}: {resp.status_code} {'OK' if passed else 'ERROR'}",
        )
    except Exception as e:
        return AssertionResult(
            name="http_available",
            passed=False,
            actual=str(e),
            expected="200-499",
            message=f"HTTP {url}: UNREACHABLE ({e})",
        )


def assert_http_unavailable(url: str, timeout: float = 2.0) -> AssertionResult:
    """Assert HTTP endpoint is unreachable or returns 5xx."""
    try:
        resp = httpx.get(url, timeout=timeout)
        passed = resp.status_code >= 500
        return AssertionResult(
            name="http_unavailable",
            passed=passed,
            actual=resp.status_code,
            expected=">= 500 or timeout",
            message=f"HTTP {url}: {resp.status_code} {'(expected failure)' if passed else '(unexpected success)'}",
        )
    except Exception:
        return AssertionResult(
            name="http_unavailable",
            passed=True,
            actual="timeout/refused",
            expected="timeout/refused",
            message=f"HTTP {url}: correctly unreachable",
        )


def assert_error_rate(
    total_requests: int, failed_requests: int, max_error_pct: float
) -> AssertionResult:
    """Assert error rate is within threshold."""
    if total_requests == 0:
        return AssertionResult(
            name="error_rate",
            passed=True,
            actual=0,
            expected=f"< {max_error_pct}%",
            message="No requests recorded",
        )
    error_pct = (failed_requests / total_requests) * 100
    passed = error_pct <= max_error_pct
    return AssertionResult(
        name="error_rate",
        passed=passed,
        actual=round(error_pct, 2),
        expected=f"< {max_error_pct}%",
        message=f"Error rate: {error_pct:.1f}% {'<=' if passed else '>'} {max_error_pct}%",
    )


def assert_data_integrity(
    check_url: str, expected_count: int, timeout: float = 5.0
) -> AssertionResult:
    """Assert data survived chaos (entity count unchanged)."""
    try:
        resp = httpx.get(check_url, timeout=timeout)
        if resp.status_code != 200:
            return AssertionResult(
                name="data_integrity",
                passed=False,
                actual=resp.status_code,
                expected=200,
                message=f"Data check failed: HTTP {resp.status_code}",
            )
        data = resp.json()
        # Handle both list and paginated responses
        if isinstance(data, list):
            actual_count = len(data)
        elif isinstance(data, dict) and "total" in data:
            actual_count = data["total"]
        else:
            actual_count = -1  # Unknown format

        passed = actual_count >= expected_count
        return AssertionResult(
            name="data_integrity",
            passed=passed,
            actual=actual_count,
            expected=f">= {expected_count}",
            message=f"Data integrity: {actual_count} entities {'>=' if passed else '<'} {expected_count}",
        )
    except Exception as e:
        return AssertionResult(
            name="data_integrity",
            passed=False,
            actual=str(e),
            expected="200",
            message=f"Data check error: {e}",
        )


def assert_graceful_degradation(
    core_url: str, degraded_url: str, timeout: float = 5.0
) -> AssertionResult:
    """Assert core functionality works while dependent service is down."""
    try:
        core_resp = httpx.get(core_url, timeout=timeout)
        core_ok = core_resp.status_code < 500
    except Exception:
        core_ok = False

    try:
        degraded_resp = httpx.get(degraded_url, timeout=timeout)
        degraded_ok = degraded_resp.status_code < 500
    except Exception:
        degraded_ok = True  # Expected to fail — that's OK

    passed = core_ok
    return AssertionResult(
        name="graceful_degradation",
        passed=passed,
        actual=f"core={'ok' if core_ok else 'fail'}, degraded={'ok' if degraded_ok else 'fail'}",
        expected="core=ok",
        message=f"Degradation: core {'OK' if core_ok else 'FAIL'}, dependent {'OK' if degraded_ok else 'DOWN (expected)'}",
    )


def assert_resource_recovery(
    before_mb: float, after_mb: float, max_growth_pct: float = 20.0
) -> AssertionResult:
    """Assert memory usage returned to baseline after chaos."""
    if before_mb == 0:
        return AssertionResult(
            name="resource_recovery",
            passed=True,
            actual=0,
            expected="baseline",
            message="No baseline memory recorded",
        )
    growth_pct = ((after_mb - before_mb) / before_mb) * 100
    passed = growth_pct <= max_growth_pct
    return AssertionResult(
        name="resource_recovery",
        passed=passed,
        actual=f"{after_mb:.1f}MB (+{growth_pct:.1f}%)",
        expected=f"< {max_growth_pct}% growth",
        message=f"Memory: {before_mb:.1f}MB → {after_mb:.1f}MB ({growth_pct:+.1f}%) {'OK' if passed else 'LEAK?'}",
    )
