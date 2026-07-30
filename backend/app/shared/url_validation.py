"""URL and input validation for SSRF prevention."""

from __future__ import annotations

import re
from urllib.parse import urlparse

# GitHub owner/repo format: alphanumeric, dots, hyphens, underscores
_GITHUB_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
_MAX_GITHUB_NAME_LEN = 100

# Private/internal IP ranges to block
_PRIVATE_NETWORKS = (
    "127.",  # loopback
    "10.",  # Class A private
    "192.168.",  # Class C private
    "169.254.",  # link-local / cloud metadata
    "0.",  # current network
    "172.16.",  # Class B private (simplified)
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
)

_BLOCKED_HOSTS = frozenset({"localhost", "metadata.google.internal", "169.254.169.254"})


def validate_github_owner(owner: str) -> str:
    """Validate GitHub owner/org name — no injection, no special chars."""
    if not owner:
        raise ValueError("Invalid GitHub owner: empty")
    if len(owner) > _MAX_GITHUB_NAME_LEN:
        raise ValueError(f"GitHub owner too long (max {_MAX_GITHUB_NAME_LEN} chars)")
    if not _GITHUB_NAME_RE.match(owner):
        raise ValueError(f"Invalid GitHub owner: {owner!r}")
    return owner


def validate_github_repo(repo: str) -> str:
    """Validate GitHub repo name — no injection, no special chars."""
    if not repo:
        raise ValueError("Invalid GitHub repo: empty")
    if len(repo) > _MAX_GITHUB_NAME_LEN:
        raise ValueError(f"GitHub repo too long (max {_MAX_GITHUB_NAME_LEN} chars)")
    if not _GITHUB_NAME_RE.match(repo):
        raise ValueError(f"Invalid GitHub repo: {repo!r}")
    return repo


def validate_url_not_internal(url: str) -> str:
    """Block URLs pointing to private/internal IPs and localhost.

    Raises ValueError if the URL targets a private network, localhost,
    or cloud metadata endpoints (SSRF protection).
    """
    parsed = urlparse(url)
    host = parsed.hostname or ""

    # Block explicit blocked hosts
    if host in _BLOCKED_HOSTS:
        raise ValueError(f"URL targets blocked host: {host}")

    # Block IPv6 loopback
    if host == "::1":
        raise ValueError("URL targets IPv6 loopback")

    # Block private IP ranges
    for prefix in _PRIVATE_NETWORKS:
        if host.startswith(prefix):
            raise ValueError(f"URL targets private/internal network: {host}")

    return url
