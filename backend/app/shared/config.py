from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App configuration loaded from env vars / .env."""

    app_name: str = "UPCP Backend"
    env: str = "local"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change_me_local_only"
    database_url: str = "postgresql+psycopg://upcp:upcp_local_change_me@localhost:5432/upcp"

    model_config = {"env_prefix": "UPCP_"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
