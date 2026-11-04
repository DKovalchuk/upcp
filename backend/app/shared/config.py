from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

# Environments where wildcard CORS is permitted
_CORS_WILDCARD_SAFE_ENVS = frozenset({"local", "test", "ci"})

# Default allowed headers for CORS (comma-separated string)
_DEFAULT_CORS_HEADERS = "Authorization,Content-Type,X-Request-ID"


def _parse_csv(value: str) -> list[str]:
    """Parse a comma-separated env var into a list, stripping whitespace."""
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """App configuration loaded from env vars / .env."""

    app_name: str = "UPCP Backend"
    env: str = "local"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change_me_local_only"
    database_url: str = Field(
        default="postgresql+psycopg://upcp:upcp_local_change_me@localhost:5432/upcp",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
    )

    # DB connection pool — defaults match the historical hardcoded values
    # in shared/database.py; overridable per env (a 50-user load profile
    # exhausted the fixed 20+10 pool with TimeoutErrors, TASK-0140)
    db_pool_size: int = Field(default=20, alias="UPCP_DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="UPCP_DB_MAX_OVERFLOW")

    # CORS — env vars: UPCP_CORS_ORIGINS, UPCP_CORS_ALLOW_HEADERS (comma-separated strings)
    cors_origins: str = Field(default="", alias="CORS_ORIGINS")
    cors_allow_headers: str = Field(default=_DEFAULT_CORS_HEADERS, alias="CORS_ALLOW_HEADERS")

    # LLM (optional)
    llm_enabled: bool = False
    llm_provider: str = "local"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_api_url: str = ""

    # Explicit middleware disable flags — safer than relying on env="test"
    disable_auth: bool = Field(default=False, alias="UPCP_DISABLE_AUTH")
    disable_rate_limit: bool = Field(default=False, alias="UPCP_DISABLE_RATE_LIMIT")

    # Per-surface rate policies (SPEC-0028 AC9, TASK-0173) — the values the
    # ``SurfaceRateLimit`` dependency enforces AFTER auth (principal-keyed);
    # the global pre-auth floor in RateLimitMiddleware keeps the historical
    # DEFAULT_LIMITS numbers (100/min per IP). Defaults match the historical
    # "default" bucket so existing deployments keep their effective limits.
    # Env names follow the UPCP_* contract (TASK-0119 prefix discipline).
    rate_limit_web_max: int = Field(default=100, alias="UPCP_RATE_LIMIT_WEB_MAX", ge=1)
    rate_limit_web_window: int = Field(default=60, alias="UPCP_RATE_LIMIT_WEB_WINDOW", ge=1)
    rate_limit_agent_max: int = Field(default=100, alias="UPCP_RATE_LIMIT_AGENT_MAX", ge=1)
    rate_limit_agent_window: int = Field(default=60, alias="UPCP_RATE_LIMIT_AGENT_WINDOW", ge=1)

    # Agent API-key TTL (SPEC-0028 D1/AC7): every newly issued key gets
    # expires_at = now + agent_token_ttl_days; keys issued before the rule
    # (expires_at NULL) are grandfathered until revoked.
    agent_token_ttl_days: int = Field(default=90, alias="UPCP_AGENT_TOKEN_TTL_DAYS", ge=1)

    # File uploads
    upload_dir: str = Field(default="data/uploads", alias="UPCP_UPLOAD_DIR")
    max_upload_size_bytes: int = Field(default=10 * 1024 * 1024, alias="UPCP_MAX_UPLOAD_SIZE")

    @model_validator(mode="after")
    def _parse_cors(self) -> Settings:
        self.__dict__["cors_origins_list"] = _parse_csv(self.cors_origins)
        self.__dict__["cors_allow_headers_list"] = _parse_csv(self.cors_allow_headers)
        return self

    @model_validator(mode="after")
    def _validate_security(self) -> Settings:
        if self.secret_key == "change_me_local_only" and self.env not in ("local", "test", "ci"):
            raise ValueError(
                "UPCP_SECRET_KEY must be set to a secure value in production. "
                "Current value is the insecure default."
            )
        cors_origins_list: list[str] = getattr(self, "cors_origins_list", [])
        if "*" in cors_origins_list and self.env not in _CORS_WILDCARD_SAFE_ENVS:
            raise ValueError(
                "CORS wildcard '*' is not allowed in production environments. "
                f"Set UPCP_CORS_ORIGINS to explicit origins. Current env: {self.env}"
            )
        return self

    model_config = {
        "env_prefix": "UPCP_",
        "extra": "ignore",
        "populate_by_name": True,
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
