import os
from unittest.mock import patch

from app.llm.gateway import DeepSeekProvider, LLMGateway, LocalProvider, OpenAIProvider
from app.shared.config import get_settings


def _clear_settings_cache():
    """Clear the lru_cache for get_settings."""
    get_settings.cache_clear()


def test_llm_gateway_disabled() -> None:
    """Test LLM gateway when LLM is disabled."""
    with patch.dict(os.environ, {"UPCP_LLM_ENABLED": "false"}):
        _clear_settings_cache()
        gateway = LLMGateway()
        assert not gateway.is_enabled


def test_llm_gateway_enabled_local() -> None:
    """Test LLM gateway with local provider."""
    with patch.dict(os.environ, {"UPCP_LLM_ENABLED": "true", "UPCP_LLM_PROVIDER": "local"}):
        _clear_settings_cache()
        gateway = LLMGateway()
        assert gateway.is_enabled
        assert isinstance(gateway._provider, LocalProvider)


def test_llm_gateway_enabled_openai() -> None:
    """Test LLM gateway with OpenAI provider."""
    with patch.dict(os.environ, {
        "UPCP_LLM_ENABLED": "true",
        "UPCP_LLM_PROVIDER": "openai",
        "UPCP_LLM_API_KEY": "test-key",
    }):
        _clear_settings_cache()
        gateway = LLMGateway()
        assert gateway.is_enabled
        assert isinstance(gateway._provider, OpenAIProvider)


def test_llm_gateway_enabled_deepseek() -> None:
    """Test LLM gateway with DeepSeek provider."""
    with patch.dict(os.environ, {
        "UPCP_LLM_ENABLED": "true",
        "UPCP_LLM_PROVIDER": "deepseek",
        "UPCP_LLM_API_KEY": "test-key",
    }):
        _clear_settings_cache()
        gateway = LLMGateway()
        assert gateway.is_enabled
        assert isinstance(gateway._provider, DeepSeekProvider)


def test_llm_gateway_unknown_provider() -> None:
    """Test LLM gateway with unknown provider."""
    with patch.dict(os.environ, {
        "UPCP_LLM_ENABLED": "true",
        "UPCP_LLM_PROVIDER": "unknown",
    }):
        _clear_settings_cache()
        try:
            LLMGateway()
            # Should raise ValueError
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Unknown LLM provider" in str(e)


def test_local_provider_generate_summary() -> None:
    """Test local provider generates summary."""
    provider = LocalProvider()
    summary = provider.generate_summary("Test text for summarization")
    assert "Summary generated locally" in summary
    assert "Test text for summarization" in summary[:100]


def test_disabled_provider_raises_error() -> None:
    """Test disabled provider raises NotImplementedError."""
    from app.llm.gateway import _DisabledProvider
    provider = _DisabledProvider()
    try:
        provider.generate_summary("Test text")
        raise AssertionError("Should have raised NotImplementedError")
    except NotImplementedError as e:
        assert "LLM is disabled" in str(e)