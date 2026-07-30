"""Tests for SSRF protection and input validation."""

import pytest
from app.gitread.adapters import GitHubAdapter
from app.gitread.schemas import GitProviderCreate
from app.shared.url_validation import (
    validate_github_owner,
    validate_github_repo,
    validate_url_not_internal,
)

# ── GitHub owner/repo validation ──────────────────────────────────


class TestValidateGithubOwner:
    def test_valid_owners(self) -> None:
        assert validate_github_owner("octocat") == "octocat"
        assert validate_github_owner("my-org") == "my-org"
        assert validate_github_owner("org.name") == "org.name"
        assert validate_github_owner("user_123") == "user_123"

    def test_empty_owner_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub owner"):
            validate_github_owner("")

    def test_injection_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub owner"):
            validate_github_owner("org; rm -rf /")

    def test_special_chars_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub owner"):
            validate_github_owner("org$(whoami)")

    def test_spaces_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub owner"):
            validate_github_owner("my org")

    def test_too_long_rejected(self) -> None:
        with pytest.raises(ValueError, match="too long"):
            validate_github_owner("a" * 101)

    def test_slash_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub owner"):
            validate_github_owner("org/repo")


class TestValidateGithubRepo:
    def test_valid_repos(self) -> None:
        assert validate_github_repo("my-repo") == "my-repo"
        assert validate_github_repo("repo.name") == "repo.name"
        assert validate_github_repo("repo_123") == "repo_123"

    def test_empty_repo_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub repo"):
            validate_github_repo("")

    def test_injection_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub repo"):
            validate_github_repo("repo; curl evil.com")


# ── Internal IP / SSRF blocking ───────────────────────────────────


class TestValidateUrlNotInternal:
    def test_public_urls_allowed(self) -> None:
        assert validate_url_not_internal("https://api.github.com/repos/org/repo")
        assert validate_url_not_internal("https://example.com/path")

    def test_localhost_blocked(self) -> None:
        with pytest.raises(ValueError, match="blocked|private|internal"):
            validate_url_not_internal("http://localhost:8080/path")

    def test_127_x_blocked(self) -> None:
        with pytest.raises(ValueError, match="blocked|private|internal"):
            validate_url_not_internal("http://127.0.0.1/admin")

    def test_10_x_blocked(self) -> None:
        with pytest.raises(ValueError, match="blocked|private|internal"):
            validate_url_not_internal("http://10.0.0.1/secret")

    def test_192_168_blocked(self) -> None:
        with pytest.raises(ValueError, match="blocked|private|internal"):
            validate_url_not_internal("http://192.168.1.1/admin")

    def test_169_254_blocked(self) -> None:
        with pytest.raises(ValueError, match="blocked|private|internal"):
            validate_url_not_internal("http://169.254.169.254/metadata")

    def test_ipv6_localhost_blocked(self) -> None:
        with pytest.raises(ValueError, match="blocked|private|internal|loopback"):
            validate_url_not_internal("http://[::1]/path")

    def test_cloud_metadata_blocked(self) -> None:
        with pytest.raises(ValueError, match="blocked|private|internal"):
            validate_url_not_internal("http://169.254.169.254/latest/meta-data/")


# ── GitHubAdapter SSRF protection ─────────────────────────────────


class TestGitHubAdapterSSRF:
    def test_valid_owner_repo_accepted(self) -> None:
        adapter = GitHubAdapter(owner="octocat", repo="Hello-World")
        assert adapter._owner == "octocat"
        assert adapter._repo == "Hello-World"

    def test_injection_owner_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub owner"):
            GitHubAdapter(owner="org; rm -rf /", repo="repo")

    def test_injection_repo_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub repo"):
            GitHubAdapter(owner="org", repo="repo; curl evil.com")


# ── GitProviderCreate schema ──────────────────────────────────────


class TestGitProviderCreateSchema:
    def test_valid_github_provider(self) -> None:
        provider = GitProviderCreate(
            name="GitHub",
            provider_type="github",
            url="https://api.github.com",
        )
        assert provider.provider_type == "github"

    def test_valid_gitlab_provider(self) -> None:
        provider = GitProviderCreate(
            name="GitLab",
            provider_type="gitlab",
            url="https://gitlab.com/api/v4",
        )
        assert provider.provider_type == "gitlab"

    def test_invalid_provider_type_rejected(self) -> None:
        with pytest.raises(Exception, match="provider_type"):
            GitProviderCreate(
                name="Evil",
                provider_type="custom_evil_type",  # type: ignore[arg-type]
                url="https://evil.com",
            )
