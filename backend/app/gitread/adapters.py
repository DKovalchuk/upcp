import subprocess
from dataclasses import dataclass
from datetime import datetime

import httpx


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
        self._path = repo_path

    def _run(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", self._path, *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
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
        output = self._run(
            "log",
            branch,
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
        self._owner = owner
        self._repo = repo
        self._base = f"https://api.github.com/repos/{owner}/{repo}"
        self._headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self._headers["Authorization"] = f"token {token}"

    def list_branches(self) -> list[RemoteBranch]:
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
