"""Application configuration loaded from environment variables / .env file."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object.

    Values are read from environment variables (see ``.env.example``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Telegram ---
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    bot_username: str = Field(default="stellarium_ai_bot", alias="BOT_USERNAME")
    run_mode: str = Field(default="polling", alias="RUN_MODE")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_path: str = Field(default="/webhook", alias="WEBHOOK_PATH")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")
    webapp_url: str = Field(default="", alias="WEBAPP_URL")

    # --- OpenAI ---
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_mock: bool = Field(default=False, alias="OPENAI_MOCK")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://stellarium:stellarium@localhost:5432/stellarium",
        alias="DATABASE_URL",
    )

    # --- Redis ---
    redis_url: str = Field(default="", alias="REDIS_URL")

    # --- Security ---
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")

    # --- Geocoding ---
    nominatim_user_agent: str = Field(
        default="stellarium-ai/1.0 (contact@example.com)",
        alias="NOMINATIM_USER_AGENT",
    )

    # --- Misc ---
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")
    free_daily_questions: int = Field(default=5, alias="FREE_DAILY_QUESTIONS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value):
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            return [int(x.strip()) for x in value.split(",") if x.strip()]
        if isinstance(value, (list, tuple)):
            return [int(x) for x in value]
        return value

    @property
    def is_webhook(self) -> bool:
        return self.run_mode.lower() == "webhook"

    @property
    def webhook_full_url(self) -> str:
        return f"{self.webhook_url.rstrip('/')}{self.webhook_path}"

    @property
    def database_url_sync(self) -> str:
        """Synchronous variant of the DB URL (used by some tooling)."""
        return self.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
