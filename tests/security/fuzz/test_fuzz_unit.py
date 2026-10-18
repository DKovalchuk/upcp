"""Hermetic unit tests for the fuzz harness and runner registry (no network)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[3]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.security.common import check, summarize  # noqa: E402
from tests.security.fuzz import harness  # noqa: E402
from tests.security.fuzz.runner import SCENARIOS, _default_out, run_suite  # noqa: E402


def test_registry_covers_contract_scenarios():
    assert set(SCENARIOS) == {"auth_bypass", "injection", "malformed"}


def test_registered_modules_import_and_expose_run():
    for meta in SCENARIOS.values():
        module = importlib.import_module(meta["module"])
        assert callable(module.run), meta["module"]


def test_sql_error_markers_detected():
    assert harness.looks_like_sql_error("psycopg2.errors.SyntaxError") is not None
    assert harness.looks_like_sql_error('{"detail": "syntax error at or near \\"x\\""}') is not None
    assert harness.looks_like_sql_error("Traceback (most recent call last)") is not None


def test_benign_bodies_not_flagged_as_sql_error():
    assert harness.looks_like_sql_error('{"detail": "project not found"}') is None
    assert harness.looks_like_sql_error("[]") is None


def test_file_leak_markers_detected():
    assert harness.looks_like_file_leak("root:x:0:0:root:/root:/bin/bash") is not None
    assert harness.looks_like_file_leak('{"detail": "Not Found"}') is None


def test_snippet_truncates_and_flattens():
    assert harness.snippet("a\n  b") == "a b"
    long = "x" * 500
    assert len(harness.snippet(long)) == harness.MAX_BODY_SNIPPET
    assert harness.snippet(long).endswith("...")


def _sample_token() -> str:
    return "eyJ_REDACTED.payload_REDACTED.signature_REDACTED"


def test_tamper_signature_changes_only_signature():
    parts = _sample_token().split(".")
    tampered = harness.tamper_signature(_sample_token()).split(".")
    assert len(tampered) == 3
    assert tampered[:2] == parts[:2]
    assert tampered[2] != parts[2]


def test_tamper_payload_changes_payload_keeps_header():
    parts = _sample_token().split(".")
    tampered = harness.tamper_payload(_sample_token()).split(".")
    assert len(tampered) == 3
    assert tampered[0] == parts[0]
    assert tampered[1] != parts[1]
    assert tampered[2] == parts[2]


def test_garbage_jwt_shape():
    token = harness.garbage_jwt()
    assert len(token.split(".")) == 3
    assert token.split(".")[2] == "fuzzed"


def test_check_and_summarize_schema():
    ok = check("a", "auth_bypass", True, expected="401", actual="401")
    bad = check("b", "injection", False, expected="no 500", actual="500", severity="high")
    doc = summarize(suite="fuzz", target="http://x", checks=[ok, bad], scenario_counts={})
    assert doc["schema"] == "upcp-security-result/v1"
    assert doc["suite"] == "fuzz"
    assert doc["summary"] == {"total": 2, "passed": 1, "failed": 1}
    assert doc["findings"][0]["severity"] == "high"
    assert doc["findings"][0]["title"] == "b"
    assert set(ok) == {"name", "category", "status", "expected", "actual", "detail", "severity"}


def test_run_suite_crash_becomes_failed_check(monkeypatch):
    def _boom(_base: str) -> list[dict]:
        raise RuntimeError("harness bug")

    monkeypatch.setitem(
        SCENARIOS, "injection", {"module": "tests.security.fuzz.scenarios.injection"}
    )
    monkeypatch.setattr(importlib, "import_module", lambda _name: type("M", (), {"run": _boom})())
    checks, counts = run_suite(["injection"])
    assert counts["injection"]["failed"] == 1
    assert checks[0]["status"] == "fail"
    assert "crashed" in checks[0]["name"]


def test_default_out_lands_in_results_dir():
    assert _default_out().parent.name == "results"
    assert _default_out().name.startswith("fuzz_")
    assert _default_out().suffix == ".json"
