"""TASK-0158 — security results → Pushgateway contract (runner side).

Red → green: runner.py grows ``build_push_body``/``push_metrics`` publishing
``upcp-security-result/v1`` docs as Prometheus gauges. Best-effort is part of
the contract: an unreachable gateway must not change the suite exit code.

The root ``tests/security/runner.py`` is loaded in the backend pytest scope
via sys.modules pre-registration — same pattern as test_zap_scan_auth.py
(pythonpath=["backend"] binds the bare name ``tests`` to backend/tests).
"""

from __future__ import annotations

import importlib.util
import sys
import types
import urllib.error
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    def load(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    pkg = types.ModuleType("tests.security")
    pkg.__path__ = [str(_REPO_ROOT / "tests" / "security")]
    sys.modules.setdefault("tests.security", pkg)
    load("tests.security.common", _REPO_ROOT / "tests" / "security" / "common.py")
    return load("tests.security.runner", _REPO_ROOT / "tests" / "security" / "runner.py")


runner = _load_runner()


def _result(suite: str = "zap", failed: int = 0, findings=(), duration=None) -> dict:
    doc = {
        "schema": "upcp-security-result/v1",
        "suite": suite,
        "target": "http://localhost:38082",
        "checks": [],
        "findings": list(findings),
        "summary": {"total": 4, "passed": 4 - failed, "failed": failed},
    }
    if duration is not None:
        doc["duration_seconds"] = duration
    return doc


class _Resp:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return b""


def test_build_push_body_exposes_all_series() -> None:
    doc = _result(
        failed=2,
        findings=[{"severity": "high", "title": "a"}, {"severity": "medium", "title": "b"}],
        duration=42,
    )
    body = runner.build_push_body(doc)

    assert "# TYPE upcp_security_pass gauge" in body
    assert 'upcp_security_pass{suite="zap"} 0' in body
    assert 'upcp_security_findings{suite="zap",severity="high"} 1' in body
    assert 'upcp_security_findings{suite="zap",severity="medium"} 1' in body
    # stable series: all four severities always present (dashboard queries)
    for sev in ("high", "medium", "low", "info"):
        assert f'severity="{sev}"' in body, f"missing stable series for {sev}"
    assert 'upcp_security_duration_seconds{suite="zap"} 42' in body
    assert 'upcp_security_timestamp{suite="zap"}' in body


def test_build_push_body_pass_flag_and_duration_omission() -> None:
    """failed==0 → pass 1; absent duration must not be published as a fake 0."""
    body = runner.build_push_body(_result(failed=0))
    assert 'upcp_security_pass{suite="zap"} 1' in body
    assert "upcp_security_duration_seconds" not in body


def test_push_metrics_puts_to_suite_grouping_key(monkeypatch) -> None:
    doc = _result()
    captured: dict = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["body"] = req.data.decode()
        return _Resp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    ok = runner.push_metrics([doc], url="http://gw:9091")

    assert ok is True
    assert captured["method"] == "PUT", "Pushgateway ingest is HTTP PUT"
    assert captured["url"] == "http://gw:9091/metrics/job/upcp_security/suite/zap"

    def _without_timestamp(body: str) -> str:
        return "\n".join(
            ln for ln in body.splitlines() if not ln.startswith("upcp_security_timestamp")
        )

    # timestamp is clock-derived — compare everything but that single line
    assert _without_timestamp(captured["body"]) == _without_timestamp(runner.build_push_body(doc))


def test_push_metrics_is_best_effort(monkeypatch, capsys) -> None:
    """Gateway down → warning on stderr, False, NO exception (gate untouched)."""

    def boom(req, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    ok = runner.push_metrics([_result()])
    assert ok is False
    assert "not published" in capsys.readouterr().err


def test_main_pushes_results_after_suite_run(monkeypatch) -> None:
    """Wiring: every completed run publishes its results, before exit."""
    import pytest

    doc = _result()
    monkeypatch.setattr(runner, "health_ok", lambda *a, **k: True)
    monkeypatch.setattr(runner, "run_suite", lambda name, host: (0, doc))
    pushed: dict = {}
    monkeypatch.setattr(
        runner,
        "push_metrics",
        lambda results, url=None: pushed.setdefault("results", list(results)) or True,
    )
    monkeypatch.setattr(sys, "argv", ["runner.py", "--suite", "zap"])

    with pytest.raises(SystemExit) as exc:
        runner.main()

    assert exc.value.code == 0
    assert pushed.get("results") == [doc], "main must push the aggregated results"
