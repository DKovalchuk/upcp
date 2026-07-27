"""Tests for hardened Git adapter — input validation."""

import pytest
from app.gitread.adapters import (
    LocalGitAdapter,
    _validate_path,
    _validate_ref,
)


class TestValidateRef:
    def test_valid_refs(self) -> None:
        assert _validate_ref("main") == "main"
        assert _validate_ref("feature/my-branch") == "feature/my-branch"
        assert _validate_ref("v1.2.3") == "v1.2.3"
        assert _validate_ref("refs/heads/main") == "refs/heads/main"

    def test_empty_ref_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid git ref"):
            _validate_ref("")

    def test_shell_injection_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid git ref"):
            _validate_ref("main; rm -rf /")

    def test_special_chars_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid git ref"):
            _validate_ref("main$(whoami)")

    def test_spaces_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid git ref"):
            _validate_ref("main branch")

    def test_too_long_rejected(self) -> None:
        with pytest.raises(ValueError, match="too long"):
            _validate_ref("a" * 256)


class TestValidatePath:
    def test_valid_path(self, tmp_path) -> None:
        result = _validate_path(str(tmp_path))
        assert result.exists()

    def test_nonexistent_path(self) -> None:
        with pytest.raises(ValueError, match="does not exist"):
            _validate_path("/nonexistent/path/12345")


class TestLocalGitAdapter:
    def test_list_branches(self, tmp_path) -> None:
        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        (tmp_path / "file.txt").write_text("initial")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)

        adapter = LocalGitAdapter(str(tmp_path))
        branches = adapter.list_branches()
        assert len(branches) >= 1
        assert any(b.is_default for b in branches)

    def test_get_commits(self, tmp_path) -> None:
        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        (tmp_path / "file.txt").write_text("initial")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "test commit"], cwd=tmp_path, capture_output=True)

        adapter = LocalGitAdapter(str(tmp_path))
        commits = adapter.get_commits()
        assert len(commits) >= 1
        assert commits[0].message == "test commit"

    def test_invalid_branch_rejected(self, tmp_path) -> None:
        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

        adapter = LocalGitAdapter(str(tmp_path))
        with pytest.raises(ValueError, match="Invalid git ref"):
            adapter.get_commits(branch="main; rm -rf /")
