"""Hardened Git adapter — validated inputs, safe subprocess calls."""

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.shared.logging import get_logger

logger = get_logger(__name__)

# Validate branch/tag names (git ref format)
_SAFE_REF_RE = re.compile(r"^[a-zA-Z0-9_./\-]+$")


def _validate_ref(ref: str) -> str:
    """Validate git ref name to prevent injection."""
    if not ref or not _SAFE_REF_RE.match(ref):
        raise ValueError(f"Invalid git ref: {ref!r}")
    if len(ref) > 255:
        raise ValueError("Git ref too long")
    return ref


def _validate_path(path: str) -> Path:
    """Validate repo path exists and is a directory."""
    p = Path(path).resolve()
    if not p.exists():
        raise ValueError(f"Repository path does not exist: {p}")
    if not p.is_dir():
        raise ValueError(f"Repository path is not a directory: {p}")
    return p


@dataclass
class RemoteBranch:
    name: str
    last_commit_sha: str
    is_default: bool


@dataclass
class RemoteCommit:
    sha: str
    message: str
    author: str
    committed_at: datetime


class LocalGitAdapter:
    def __init__(self, repo_path: str) -> None:
        self._path = _validate_path(repo_path)

    def _run(self, *args: str) -> str:
        """Run git command safely with validated inputs."""
        cmd = ["git", "-C", str(self._path), *args]
        logger.debug(f"Running: git -C {self._path} {' '.join(args[:3])}...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timed out: {args[0]}")
            raise RuntimeError(f"git {args[0]} timed out") from None

        if result.returncode != 0:
            stderr = result.stderr.strip()
            logger.error(f"Git command failed: {args[0]} — {stderr[:200]}")
            raise RuntimeError(f"git {args[0]} failed")

        return result.stdout.strip()

    def list_branches(self) -> list[RemoteBranch]:
        default = self._run("symbolic-ref", "--short", "HEAD")
        output = self._run("branch", "--format=%(refname:short)|%(objectname:short)")
        branches = []
        for line in output.splitlines():
            if not line:
                continue
            parts = line.split("|")
            name = parts[0]
            sha = parts[1] if len(parts) > 1 else ""
            branches.append(
                RemoteBranch(name=name, last_commit_sha=sha, is_default=(name == default))
            )
        return branches

    def get_commits(self, branch: str = "HEAD", limit: int = 20) -> list[RemoteCommit]:
        validated_branch = _validate_ref(branch)
        limit = max(1, min(limit, 100))  # Clamp 1-100

        output = self._run(
            "log",
            validated_branch,
            f"--max-count={limit}",
            "--format=%H|%s|%an|%aI",
        )
        commits = []
        for line in output.splitlines():
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) < 4:
                continue
            commits.append(
                RemoteCommit(
                    sha=parts[0],
                    message=parts[1],
                    author=parts[2],
                    committed_at=datetime.fromisoformat(parts[3]),
                )
            )
        return commits


class GitHubAdapter:
    def __init__(self, owner: str, repo: str, token: str | None = None) -> None:
        from app.shared.url_validation import validate_github_owner, validate_github_repo

        self._owner = validate_github_owner(owner)
        self._repo = validate_github_repo(repo)
        self._base = f"https://api.github.com/repos/{self._owner}/{self._repo}"
        self._headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self._headers["Authorization"] = f"token {token}"

    def list_branches(self) -> list[RemoteBranch]:
        import httpx

        with httpx.Client(headers=self._headers, timeout=30) as client:
            resp = client.get(f"{self._base}/branches")
            resp.raise_for_status()
            default_resp = client.get(f"{self._base}")
            default_branch = default_resp.json().get("default_branch", "main")
            return [
                RemoteBranch(
                    name=b["name"],
                    last_commit_sha=b["commit"]["sha"],
                    is_default=(b["name"] == default_branch),
                )
                for b in resp.json()
            ]

    def get_commits(self, branch: str = "main", limit: int = 20) -> list[RemoteCommit]:
        import httpx

        with httpx.Client(headers=self._headers, timeout=30) as client:
            resp = client.get(f"{self._base}/commits", params={"sha": branch, "per_page": limit})
            resp.raise_for_status()
            return [
                RemoteCommit(
                    sha=c["sha"],
                    message=c["commit"]["message"].split("\n")[0],
                    author=c["commit"]["author"]["name"] or "unknown",
                    committed_at=datetime.fromisoformat(
                        c["commit"]["author"]["date"].replace("Z", "+00:00")
                    ),
                )
                for c in resp.json()
            ]
