from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "Finance Tracker API"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/finance_tracker"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/finance_tracker"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit_auth: str = "10/minute"
    goal_deadline_warning_days: int = 7
    budget_warning_threshold: float = 0.8
    api_v1_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
