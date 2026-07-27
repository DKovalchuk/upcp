"""Secret provider abstraction — env, file, future vault."""

import os
from abc import ABC, abstractmethod
from pathlib import Path

from app.shared.logging import get_logger

logger = get_logger(__name__)


class SecretProvider(ABC):
    """Abstract base for secret providers."""

    @abstractmethod
    def get(self, key: str, default: str | None = None) -> str | None:
        """Get a secret value by key."""

    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if a secret exists."""


class EnvSecretProvider(SecretProvider):
    """Read secrets from environment variables."""

    def get(self, key: str, default: str | None = None) -> str | None:
        value = os.environ.get(key, default)
        if value is not None:
            logger.debug(f"Secret loaded from env: {key}")
        return value

    def has(self, key: str) -> bool:
        return key in os.environ


class FileSecretProvider(SecretProvider):
    """Read secrets from files (e.g., Docker secrets, Kubernetes secrets)."""

    def __init__(self, base_path: str = "/run/secrets") -> None:
        self._base_path = Path(base_path)

    def get(self, key: str, default: str | None = None) -> str | None:
        secret_file = self._base_path / key
        if secret_file.exists():
            value = secret_file.read_text().strip()
            logger.debug(f"Secret loaded from file: {key}")
            return value
        return default

    def has(self, key: str) -> bool:
        return (self._base_path / key).exists()


class CompositeSecretProvider(SecretProvider):
    """Try multiple providers in order (file first, then env)."""

    def __init__(self, providers: list[SecretProvider]) -> None:
        self._providers = providers

    def get(self, key: str, default: str | None = None) -> str | None:
        for provider in self._providers:
            if provider.has(key):
                return provider.get(key, default)
        return default

    def has(self, key: str) -> bool:
        return any(p.has(key) for p in self._providers)


def get_secret_provider() -> SecretProvider:
    """Get the configured secret provider."""
    return CompositeSecretProvider(
        [
            FileSecretProvider("/run/secrets"),
            EnvSecretProvider(),
        ]
    )
