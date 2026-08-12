"""LLM gateway — routes summary requests to the configured provider.

When no LLM API key is configured, requests raise NotImplementedError
so the endpoint can return 501 instead of silently returning fake data.
"""

import logging
from abc import ABC, abstractmethod

from app.shared.config import get_settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_summary(self, text: str) -> str:
        """Generate a summary from text."""
        ...


class _NullProvider(LLMProvider):
    """Provider used when LLM is not configured.

    Raises ``NotImplementedError`` so callers can return 501 instead of
    silently producing fabricated summaries.
    """

    def generate_summary(self, text: str) -> str:
        raise NotImplementedError(
            "LLM not configured. Set UPCP_LLM_API_KEY and UPCP_LLM_PROVIDER to enable LLM features."
        )


class OpenAIProvider(LLMProvider):
    """OpenAI API provider — requires a real API key and network access."""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo") -> None:
        self.api_key = api_key
        self.model = model

    def generate_summary(self, text: str) -> str:
        # TODO: implement real OpenAI API call via httpx
        raise NotImplementedError("OpenAI provider not yet implemented")


class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider — requires a real API key and network access."""

    def __init__(self, api_key: str, model: str = "deepseek-chat") -> None:
        self.api_key = api_key
        self.model = model

    def generate_summary(self, text: str) -> str:
        # TODO: implement real DeepSeek API call via httpx
        raise NotImplementedError("DeepSeek provider not yet implemented")


class LocalProvider(LLMProvider):
    """Local model provider — requires a running Ollama or compatible server."""

    def generate_summary(self, text: str) -> str:
        # TODO: implement local model integration
        raise NotImplementedError("Local provider not yet implemented")


class LLMGateway:
    """Gateway for LLM operations with provider selection."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._provider = self._create_provider()

    def _create_provider(self) -> LLMProvider:
        """Create the appropriate LLM provider based on configuration."""
        if not self._settings.llm_enabled:
            return _NullProvider()

        provider_name = self._settings.llm_provider.lower()
        api_key = self._settings.llm_api_key
        model = self._settings.llm_model

        if provider_name == "local":
            return LocalProvider()
        elif provider_name in ("openai", "deepseek"):
            if not api_key:
                logger.warning(
                    "LLM provider %s enabled but UPCP_LLM_API_KEY not set", provider_name
                )
                return _NullProvider()
            if provider_name == "openai":
                return OpenAIProvider(api_key=api_key, model=model or "gpt-3.5-turbo")
            return DeepSeekProvider(api_key=api_key, model=model or "deepseek-chat")
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    def generate_summary(self, text: str) -> str:
        """Generate a summary using the configured provider."""
        return self._provider.generate_summary(text)

    @property
    def is_enabled(self) -> bool:
        """Check if LLM is enabled.

        Local provider works without an API key; remote providers need one.
        """
        if not self._settings.llm_enabled:
            return False
        if self._settings.llm_provider.lower() == "local":
            return True
        return bool(self._settings.llm_api_key)
