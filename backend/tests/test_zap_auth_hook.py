"""TASK-0157 — behaviour of the GENERATED authenticated-baseline hook.

The wrapper contract lives in test_zap_scan_auth.py; this module exec's
the generated hook the same way zap_common.load_custom_hooks does
(SourceFileLoader on the file in /zap/wrk) and fakes its three
collaborators:

* login mint       -> urllib.request.urlopen (records url + body)
* ZAP proxy fetch  -> urllib.request.build_opener (records probed urls)
* status file      -> builtins.open (the /zap/wrk path must not exist here)

Why: a wrong hook surfaces only in a multi-minute live env-lifecycle run;
these tests pin the strict contract (rule must land, 401/403 = header not
injected = failure, mint failure = failure, no token in output) cheaply.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from tests.test_zap_scan_auth import zap_scan

TARGET = "http://app:8080"
PROBE_CODES_OK = {
    "http://app:8080/": 404,  # backend root has no route — tolerated, not auth
    "http://app:8080/api/v1/projects": 200,
    "http://app:8080/api/v1/agents": 200,
    "http://app:8080/api/v1/analytics/agents/overview": 200,
}


class _Replacer:
    def __init__(self, result: str = "ok") -> None:
        self.result = result
        self.calls: list[dict] = []

    def add_rule(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class _Zap:
    """Client stand-in: script-built proxy address + replacer category."""

    def __init__(self, replacer_result: str = "ok") -> None:
        self.replacer = _Replacer(replacer_result)
        # attribute name of the real ZAPv2 instance (_ZAPv2__proxies);
        # single leading underscore — no mangling in this class either.
        self._ZAPv2__proxies = {"http": "http://127.0.0.1:39123"}


def _run_hook(monkeypatch, *, zap, code_by_url, mint_error=None):
    """Exec the generated hook; return (status_text, captured)."""
    src = zap_scan.render_auth_hook(zap_scan.load_config())
    captured: dict = {}

    class _StatusSink:
        def __init__(self) -> None:
            self.data = ""

        def write(self, chunk: str) -> None:
            self.data += chunk

        def close(self) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_open(path, mode="r", **kwargs):
        assert str(path).endswith("zap_auth_hook_status.txt"), f"unexpected open: {path}"
        assert "w" in mode, "the hook only writes the status file"
        sink = _StatusSink()
        captured["sink"] = sink
        return sink

    class _MintResp:
        def read(self) -> bytes:
            return json.dumps({"access_token": "tok-123"}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout=None):
        captured["mint_url"] = req.full_url
        captured["mint_body"] = json.loads(req.data.decode())
        if mint_error is not None:
            raise mint_error
        return _MintResp()

    class _ProbeResp:
        def __init__(self, code: int) -> None:
            self._code = code

        def getcode(self) -> int:
            return self._code

        def close(self) -> None:
            pass

    def fake_build_opener(*handlers):
        captured["proxy"] = getattr(handlers[0], "proxies", {}).get("http")

        class _Opener:
            def open(self, req, timeout=None):
                url = req.full_url
                captured.setdefault("probe_urls", []).append(url)
                code = code_by_url.get(url, 404)
                if code >= 400:
                    raise urllib.error.HTTPError(url, code, "err", {}, None)
                return _ProbeResp(code)

        return _Opener()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(urllib.request, "build_opener", fake_build_opener)

    import builtins

    fake_builtins = vars(builtins).copy()
    fake_builtins["open"] = fake_open
    ns: dict = {"__builtins__": fake_builtins}
    exec(compile(src, "zap_auth_hook_generated.py", "exec"), ns)
    ns["zap_started"](zap, TARGET)
    return captured["sink"].data.strip(), captured


def _env(monkeypatch) -> None:
    auth = zap_scan.load_config()["auth"]
    monkeypatch.setenv(auth["env_user"], "admin@example.com")
    monkeypatch.setenv(auth["env_password"], "TestAdmin123!")


def test_hook_adds_rule_and_probes_through_proxy(monkeypatch, capsys) -> None:
    _env(monkeypatch)
    zap = _Zap()
    status, captured = _run_hook(monkeypatch, zap=zap, code_by_url=PROBE_CODES_OK)

    assert status.startswith("ok header=replacer probes=4")
    assert "codes=404,200,200,200" in status, "tolerated 404 on / must be visible"

    call = zap.replacer.calls[0]
    assert call["matchtype"] == "REQ_HEADER"
    assert call["matchstring"] == "Authorization"
    assert call["replacement"] == "Bearer tok-123"
    assert call["enabled"] == "true"

    assert captured["mint_url"] == "http://app:8080/auth/login"
    assert captured["mint_body"] == {"email": "admin@example.com", "password": "TestAdmin123!"}
    assert captured["proxy"] == "http://127.0.0.1:39123", "probes use the client proxy address"
    assert len(captured["probe_urls"]) == 4

    out = capsys.readouterr().out
    assert "auth_hook: minted token (REDACTED)" in out
    assert "tok-123" not in out, "minted token must never be printed"


def test_hook_fails_when_replacer_rejects_rule(monkeypatch) -> None:
    """Component/API mismatch must fail loudly — no probes without a rule."""
    _env(monkeypatch)
    zap = _Zap(replacer_result="no_component")
    status, captured = _run_hook(monkeypatch, zap=zap, code_by_url=PROBE_CODES_OK)

    assert status.startswith("error header:")
    assert "no_component" in status
    assert "probe_urls" not in captured, "must not probe when the rule did not land"


def test_hook_fails_when_probe_unauthorized(monkeypatch) -> None:
    """401 from a probe = the Authorization header was NOT injected."""
    _env(monkeypatch)
    zap = _Zap()
    codes = {**PROBE_CODES_OK, "http://app:8080/api/v1/projects": 401}
    status, _captured = _run_hook(monkeypatch, zap=zap, code_by_url=codes)

    assert status.startswith("error probe")
    assert "/api/v1/projects: HTTP 401" in status


def test_hook_fails_when_login_unreachable(monkeypatch) -> None:
    """Mint failure = broken authenticated baseline (strict, no fallback)."""
    _env(monkeypatch)
    zap = _Zap()
    err = urllib.error.URLError("connection refused")
    status, captured = _run_hook(monkeypatch, zap=zap, code_by_url={}, mint_error=err)

    assert status.startswith("error URLError")
    assert zap.replacer.calls == [], "no rule without a token"
    assert "probe_urls" not in captured
