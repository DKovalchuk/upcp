import subprocess
from dataclasses import dataclass
from datetime import datetime


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
            branches.append(RemoteBranch(name=name, last_commit_sha=sha, is_default=(name == default)))
        return branches

    def get_commits(self, branch: str = "HEAD", limit: int = 20) -> list[RemoteCommit]:
        output = self._run(
            "log", branch, f"--max-count={limit}",
            "--format=%H|%s|%an|%aI",
        )
        commits = []
        for line in output.splitlines():
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) < 4:
                continue
            commits.append(RemoteCommit(
                sha=parts[0],
                message=parts[1],
                author=parts[2],
                committed_at=datetime.fromisoformat(parts[3]),
            ))
        return commits
