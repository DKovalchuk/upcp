"""Config-example auth kill-switch contract — SPEC-0028 §7 promise (review FIX 10).

``UPCP_DISABLE_AUTH=true`` is the documented test-only hermetic kill switch
(AC10). SPEC-0028 §7 promises it never ships in a deployable config: no
TRACKED env/compose example may set it truthy — a demo or compose edit must
not silently disable auth in an environment that gets deployed.

Red first: ``_violations`` starts as a ``NotImplementedError`` stub, so both
behavioral tests fail until the scanner is implemented in this file.
"""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Root-level tracked config examples (task list: .env.example, .env.stage.example,
# docker-compose*.yml — the patterns cover every current and future sibling).
_FILE_PATTERNS = (".env*", "docker-compose*.y*ml")
_TRUTHY = frozenset({"true", "1", "yes", "on"})


def _config_files() -> list[Path]:
    """Root-level TRACKED config examples (git-ls-files — untracked local
    ``.env`` copies are developer state, not shipped examples)."""
    # CI's shared /builds checkout carries mixed ownership (quality:gate chowns
    # `.`/frontend/tests to uid 1000, .git stays root) → git's dubious-ownership
    # guard exits 128. Command-line safe.directory scopes the bypass to this
    # one read-only ls-files call.
    proc = subprocess.run(
        ["git", "-c", "safe.directory=*", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    names = [
        line
        for line in proc.stdout.splitlines()
        if "/" not in line and any(fnmatch.fnmatch(line, p) for p in _FILE_PATTERNS)
    ]
    return sorted(REPO_ROOT / n for n in names)


def _violations(text: str) -> list[int]:
    """Line numbers where UPCP_DISABLE_AUTH is set to a truthy value.

    Parses both ``KEY=value`` (env) and ``KEY: value`` / ``- KEY=value``
    (compose) shapes; comment lines never set anything.
    """
    violations: list[int] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "UPCP_DISABLE_AUTH" not in stripped:
            continue
        _, sep, value = stripped.partition("=")
        if not sep:
            _, sep, value = stripped.partition(":")
        if not sep:
            continue  # bare mention (e.g. a docs line) — nothing is set
        # strip compose quoting / trailing comment noise
        value = value.split("#", 1)[0].strip().strip("'\"").strip()
        if value.lower() in _TRUTHY:
            violations.append(lineno)
    return violations


def test_scan_covers_the_known_config_examples() -> None:
    """The scan must be non-vacuous: the canonical examples are in scope."""
    names = {p.name for p in _config_files()}
    assert ".env.example" in names, names
    assert "docker-compose.yml" in names, names


def test_tracked_config_examples_never_enable_auth_bypass() -> None:
    files = _config_files()
    assert files, "config-example scan must not be empty"
    for path in files:
        violations = _violations(path.read_text(encoding="utf-8"))
        assert not violations, (
            f"{path.name}: UPCP_DISABLE_AUTH set truthy at line(s) {violations} — "
            f"SPEC-0028 §7: shipped examples keep auth ON"
        )


def test_scanner_flags_truthy_but_allows_false_and_absent() -> None:
    assert _violations("UPCP_DISABLE_AUTH=true") != [], "true must be flagged"
    assert _violations('UPCP_DISABLE_AUTH: "true"') != [], "quoted true must be flagged"
    assert _violations("UPCP_DISABLE_AUTH=false") == [], "false is allowed"
    assert _violations("# UPCP_DISABLE_AUTH=true") == [], "comments never set anything"
    assert _violations("") == [], "absent is allowed"
