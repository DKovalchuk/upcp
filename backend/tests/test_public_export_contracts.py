"""Pre-publish hygiene contracts — TASK-0167.

Scanned tracked files must not carry live-looking secrets: the stage stack
secret has to arrive via compose interpolation (from an untracked env file
or a masked CI variable), and security test artifacts must not embed
expired-but-real JWTs from the local test stack.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

STAGE_COMPOSE = ROOT / "docker-compose.stage.yml"
ENV_STAGE = ROOT / ".env.stage"
ENV_STAGE_EXAMPLE = ROOT / ".env.stage.example"
GITIGNORE = ROOT / ".gitignore"

# Real (expired, local-stack) secret that lived hardcoded in the stage files.
LEAKED_STAGE_SECRET = "REDACTED_STAGE_SECRET"

JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")

SECURITY_ARTIFACT_DIRS = (
    ROOT / "tests" / "security" / "reports",
    ROOT / "tests" / "security" / "results",
)
SECURITY_ARTIFACT_SUFFIXES = {".md", ".json", ".xml", ".log", ".html"}


def test_stage_compose_interpolates_secret_key() -> None:
    # spec: stage compose uses interpolation, not a hardcoded secret
    text = STAGE_COMPOSE.read_text(encoding="utf-8")
    assert LEAKED_STAGE_SECRET not in text, (
        "docker-compose.stage.yml still hardcodes UPCP_SECRET_KEY"
    )
    assert "${UPCP_SECRET_KEY:?" in text, (
        "docker-compose.stage.yml must interpolate UPCP_SECRET_KEY with a :? hint"
    )


def test_env_stage_is_gitignored_and_not_tracked() -> None:
    # spec: .env.stage is untracked, an example file is tracked
    gitignore = GITIGNORE.read_text(encoding="utf-8")
    assert ".env.stage" in gitignore, ".env.stage missing from .gitignore"
    if shutil.which("git"):
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", ".env.stage"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert result.returncode != 0, ".env.stage is still tracked by git"


def test_env_stage_example_has_placeholder_only() -> None:
    # spec: .env.stage.example is tracked and contains no valid secret value
    assert ENV_STAGE_EXAMPLE.exists(), ".env.stage.example must be tracked"
    lines = [
        line.strip()
        for line in ENV_STAGE_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("UPCP_SECRET_KEY=")
    ]
    assert lines, ".env.stage.example must define UPCP_SECRET_KEY for copy-paste"
    value = lines[0].split("=", 1)[1].strip().strip('"').strip("'")
    assert value == "", ".env.stage.example must ship an empty UPCP_SECRET_KEY (generate locally)"
    assert LEAKED_STAGE_SECRET not in ENV_STAGE_EXAMPLE.read_text(encoding="utf-8")


@pytest.mark.parametrize("directory", SECURITY_ARTIFACT_DIRS, ids=lambda p: p.name)
def test_security_artifacts_contain_no_jwts(directory: Path) -> None:
    # spec: security reports contain no JWT-shaped strings
    if not directory.exists():
        pytest.skip(f"{directory.name} not present in this checkout")
    offenders = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix not in SECURITY_ARTIFACT_SUFFIXES:
            continue
        if path.suffix == ".html":
            # ZAP/Kali HTML reports are vendor-formatted evidence; the token
            # contract below targets the human-readable/md/json/xml artifacts
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if JWT_PATTERN.search(text):
            offenders.append(path.relative_to(ROOT))
    assert not offenders, f"JWT-shaped strings found in: {', '.join(map(str, offenders))}"
