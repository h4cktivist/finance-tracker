from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _compose_database_urls(
    user: str, password: str, host: str, port: int, db: str
) -> tuple[str, str]:
    u = quote_plus(user)
    p = quote_plus(password)
    async_url = f"postgresql+asyncpg://{u}:{p}@{host}:{port}/{db}"
    sync_url = f"postgresql://{u}:{p}@{host}:{port}/{db}"
    return async_url, sync_url


def _async_url_to_sync(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )
    app_name: str = "Finance Tracker API"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Явные URL (если заданы в .env — имеют приоритет). Иначе собираются из POSTGRES_* ниже.
    database_url: str | None = Field(default=None)
    database_url_sync: str | None = Field(default=None)

    postgres_user: str = Field(default="postgres", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="finance_tracker", validation_alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")

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

    @model_validator(mode="after")
    def _resolve_database_urls(self):
        if self.database_url:
            if not self.database_url_sync:
                object.__setattr__(
                    self,
                    "database_url_sync",
                    _async_url_to_sync(self.database_url),
                )
            return self
        async_url, sync_url = _compose_database_urls(
            self.postgres_user,
            self.postgres_password,
            self.postgres_host,
            self.postgres_port,
            self.postgres_db,
        )
        object.__setattr__(self, "database_url", async_url)
        object.__setattr__(self, "database_url_sync", sync_url)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
