"""TASK-0157 — ZAP authenticated baseline contract (hook + login-mint).

The stable ZAP scripts have no ``-H`` flag (verified against the image),
so authenticated coverage is delivered by a generated ``--hook`` file:
the hook mints a JWT via POST <target>/auth/login (creds from env, never
embedded), attaches it as a global Authorization header through a ZAP
REPLACER rule (match type REQ_HEADER — official semantics "add if not
present"; network.addHttpRequestHeader exists neither in python-zap
v0.6.0 nor in the ZAP 2.17.0 API — both probed), and force-fetches the
configured probe URLs THROUGH the ZAP proxy (the classic spider does not
walk JSON APIs; the HTTP status proves the injected header was accepted).
"""

from __future__ import annotations

import importlib.util
import json
import shlex
import sys
import types
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_zap_scan():
    """Load the root tests/security/dast/zap_scan.py module in the backend suite.

    In the backend pytest scope the name `tests` resolves to backend/tests
    (pyproject pythonpath=["backend"]), so the canonical
    `tests.security.dast` path is unreachable and collides with that
    binding. Pre-registering the middle/leaf keys in sys.modules makes
    zap_scan's internal `from tests.security.common import ...` hit the
    module cache (leaf hit short-circuits parent imports) while the
    existing `tests` binding is never touched. Validated by probe.
    """

    def load(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    security_pkg = types.ModuleType("tests.security")
    security_pkg.__path__ = [str(_REPO_ROOT / "tests" / "security")]
    sys.modules.setdefault("tests.security", security_pkg)
    load("tests.security.common", _REPO_ROOT / "tests" / "security" / "common.py")
    return load(
        "tests.security.dast.zap_scan",
        _REPO_ROOT / "tests" / "security" / "dast" / "zap_scan.py",
    )


zap_scan = _load_zap_scan()

AUTH_SECTION_KEYS = ("enabled", "login_path", "probe_urls")


def test_config_declares_auth_section() -> None:
    auth = zap_scan.load_config()["auth"]  # red: KeyError until implemented
    for key in AUTH_SECTION_KEYS:
        assert key in auth, f"auth.{key} missing from zap_config.yaml"
    assert auth["probe_urls"], "auth.probe_urls must seed authenticated API coverage"
    assert auth["login_path"].startswith("/"), "login_path is a path on the scan target"


def test_render_auth_hook_contract() -> None:
    cfg = zap_scan.load_config()
    src = zap_scan.render_auth_hook(cfg)  # red: AttributeError until implemented

    # behaviour markers
    assert "Authorization" in src
    assert "Bearer" in src
    assert cfg["auth"]["login_path"] in src
    assert "os.environ" in src, "credentials must be read from env at runtime"
    # global header via the replacer REQ_HEADER rule ("add if not present");
    # network.addHttpRequestHeader is absent from python-zap v0.6.0 AND from
    # the ZAP 2.17.0 API (both probed) — see tasks/TASK-0157.
    assert "replacer" in src and "add_rule" in src, "header injected via replacer.add_rule"
    assert "REQ_HEADER" in src, "match type that adds the header when absent"
    # probes fetch THROUGH the ZAP proxy (client transport) and read the status
    assert "ProxyHandler" in src and "_ZAPv2__proxies" in src, "probes use the client proxy"
    assert "401" in src and "403" in src, "unauthenticated probe must fail strictly"
    for url in cfg["auth"]["probe_urls"]:
        assert url in src, f"probe url {url} not in hook"

    # secrets never embedded in the generated file
    assert "TestAdmin123" not in src, "password literal leaked into hook source"
    assert "admin@example.com" not in src, "login literal leaked into hook source"


def test_build_command_with_hook_adds_flag() -> None:
    cmd = zap_scan.build_command(
        "baseline",
        "http://app:8080",
        1,
        "r.html",
        "r.json",
        None,
        {},
        Path("/tmp"),
        hook_name="zap_auth_hook_1.py",  # red: TypeError (unexpected kwarg)
    )
    # --hook is an option of zap-baseline.py *inside* `sh -c`, so it lives
    # in the shell string element, not as a separate docker argv entry.
    shell = cmd[cmd.index("-c") + 1]
    assert "--hook" in shell
    assert "/zap/wrk/zap_auth_hook_1.py" in shell


def test_build_command_without_hook_keeps_legacy_shape() -> None:
    cmd = zap_scan.build_command(
        "baseline", "http://app:8080", 1, "r.html", "r.json", None, {}, Path("/tmp")
    )
    assert "--hook" not in cmd


def _fake_zap_run(captured: dict, write_status: bool = True):
    """subprocess.run stand-in: record the command, fabricate the ZAP report.

    Mirrors the real hook contract: when the scan runs with --hook, the hook
    leaves an auth status file in the mounted report dir.
    """

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        # zap options (-J …, --hook …) live inside the `sh -c` script; only
        # docker-level flags (-v …) are top-level argv entries.
        tokens = shlex.split(cmd[cmd.index("-c") + 1])
        json_name = tokens[tokens.index("-J") + 1]
        volume = cmd[cmd.index("-v") + 1]
        report_dir = Path(volume.split(":", 1)[0])
        (report_dir / json_name).write_text('{"site": []}\n', encoding="utf-8")
        if "--hook" in tokens and write_status:
            (report_dir / "zap_auth_hook_status.txt").write_text(
                "ok minted probes=4\n", encoding="utf-8"
            )

        class _Proc:
            returncode = 0
            stdout = ""
            stderr = ""

        return _Proc()

    return fake_run


def test_main_generates_hook_and_cleans_it_up(tmp_path: Path, monkeypatch) -> None:
    report_dir = tmp_path / "reports"
    out = tmp_path / "result.json"
    captured: dict = {}
    monkeypatch.setattr(zap_scan.subprocess, "run", _fake_zap_run(captured))

    rc = zap_scan.main(["--out", str(out), "--report-dir", str(report_dir)])

    assert rc == 0
    assert "--hook" in captured["cmd"][captured["cmd"].index("-c") + 1], (
        "auth enabled (default) must wire --hook into the scan script"
    )
    # hook existed during the scan (volume path) and is removed afterwards
    assert list(report_dir.glob("zap_auth_hook_*.py")) == [], "hook file must be cleaned up"
    result = json.loads(out.read_text())
    assert result["suite"] == "zap"


def test_main_auth_disabled_keeps_unauthenticated_command(tmp_path: Path, monkeypatch) -> None:
    cfg = zap_scan.load_config()
    cfg["auth"] = {**cfg["auth"], "enabled": False}
    monkeypatch.setattr(zap_scan, "load_config", lambda: cfg)
    report_dir = tmp_path / "reports"
    out = tmp_path / "result.json"
    captured: dict = {}
    monkeypatch.setattr(zap_scan.subprocess, "run", _fake_zap_run(captured))

    rc = zap_scan.main(["--out", str(out), "--report-dir", str(report_dir)])

    assert rc == 0
    assert "--hook" not in " ".join(cmd for cmd in captured["cmd"] if isinstance(cmd, str))


def test_main_fails_when_auth_status_missing(tmp_path: Path, monkeypatch) -> None:
    """Strict contract: auth on + no ok-status file from the hook -> infra (2).

    A silent unauthenticated fallback would defeat the whole point of the
    authenticated baseline (broken login must fail the suite, not degrade it).
    """
    report_dir = tmp_path / "reports"
    out = tmp_path / "result.json"
    captured: dict = {}
    monkeypatch.setattr(zap_scan.subprocess, "run", _fake_zap_run(captured, write_status=False))

    rc = zap_scan.main(["--out", str(out), "--report-dir", str(report_dir)])

    assert rc == 2, "missing auth status must be an infra failure, not a quiet pass"
