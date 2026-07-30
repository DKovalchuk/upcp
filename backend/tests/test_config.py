from app.shared.config import Settings, get_settings


def test_settings_loads_defaults(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.delenv("UPCP_ENV", raising=False)
    monkeypatch.delenv("UPCP_DEBUG", raising=False)
    settings = Settings()
    assert settings.app_name == "UPCP Backend"
    assert settings.env == "local"
    assert settings.debug is False


def test_settings_reads_from_env(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("UPCP_ENV", "test")
    monkeypatch.setenv("UPCP_DEBUG", "true")
    settings = Settings()
    assert settings.env == "test"
    assert settings.debug is True


def test_get_settings_returns_singleton() -> None:
    a = get_settings()
    b = get_settings()
    assert a is b


# ── CORS configuration tests ──────────────────────────────────────


def test_cors_origins_default_empty(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.delenv("UPCP_CORS_ORIGINS", raising=False)
    monkeypatch.delenv("UPCP_ENV", raising=False)
    settings = Settings()
    assert settings.cors_origins_list == []


def test_cors_origins_parsed_from_env(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("UPCP_CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    monkeypatch.delenv("UPCP_ENV", raising=False)
    settings = Settings()
    assert settings.cors_origins_list == ["http://localhost:5173", "http://localhost:3000"]


def test_cors_origins_single_value(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("UPCP_CORS_ORIGINS", "https://app.example.com")
    monkeypatch.delenv("UPCP_ENV", raising=False)
    settings = Settings()
    assert settings.cors_origins_list == ["https://app.example.com"]


def test_cors_origins_strips_whitespace(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("UPCP_CORS_ORIGINS", " http://a.com , http://b.com ")
    monkeypatch.delenv("UPCP_ENV", raising=False)
    settings = Settings()
    assert settings.cors_origins_list == ["http://a.com", "http://b.com"]


def test_cors_wildcard_rejected_in_production(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("UPCP_ENV", "production")
    monkeypatch.setenv("UPCP_SECRET_KEY", "secure-production-key-123")
    monkeypatch.setenv("UPCP_CORS_ORIGINS", "*")
    import pytest

    with pytest.raises(ValueError, match="wildcard"):
        Settings()


def test_cors_wildcard_allowed_in_local(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("UPCP_ENV", "local")
    monkeypatch.setenv("UPCP_CORS_ORIGINS", "*")
    settings = Settings()
    assert settings.cors_origins_list == ["*"]


def test_cors_wildcard_allowed_in_test(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("UPCP_ENV", "test")
    monkeypatch.setenv("UPCP_CORS_ORIGINS", "*")
    settings = Settings()
    assert settings.cors_origins_list == ["*"]


def test_cors_allow_headers_defaults(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.delenv("UPCP_CORS_ALLOW_HEADERS", raising=False)
    monkeypatch.delenv("UPCP_ENV", raising=False)
    settings = Settings()
    assert "Authorization" in settings.cors_allow_headers_list
    assert "Content-Type" in settings.cors_allow_headers_list
    assert "X-Request-ID" in settings.cors_allow_headers_list
