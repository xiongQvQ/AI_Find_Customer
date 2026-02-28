"""License server configuration."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/license_db"

    # JWT signing secret (generate with: openssl rand -hex 32)
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    # Token validity
    token_ttl_days: int = 7          # client token valid for 7 days offline
    license_key_length: int = 25     # AIHNT-XXXXX-XXXXX-XXXXX-XXXXX

    # Admin API key (for generating license keys via admin API)
    admin_api_key: str = "change-me-admin-key"

    # App info
    app_name: str = "AI Hunter"
    app_version: str = "1.0.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
