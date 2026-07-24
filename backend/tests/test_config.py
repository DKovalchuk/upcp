from app.shared.config import Settings, get_settings


def test_settings_loads_defaults() -> None:
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
