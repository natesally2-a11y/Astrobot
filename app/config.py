"""Application configuration.

Settings are loaded from environment variables (with a ``.env`` file fallback
for local development).  All settings are typed via Pydantic so misconfiguration
fails fast at startup instead of deep inside the bot loop.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: str = Field(default="", alias="BOT_TOKEN")
    bot_username: str = Field(default="stellarium_ai_bot", alias="BOT_USERNAME")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_secret: str = Field(default="stellarium-webhook", alias="WEBHOOK_SECRET")
    use_webhook: bool = Field(default=False, alias="USE_WEBHOOK")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    database_url: str = Field(
        default="postgresql+asyncpg://stellarium:stellarium@localhost:5432/stellarium",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    secret_key: str = Field(default="dev-secret-key-change-me", alias="SECRET_KEY")

    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    ephemeris_path: str = Field(default="./ephemeris", alias="EPHEMERIS_PATH")

    pro_price_stars: int = Field(default=50, alias="PRO_PRICE_STARS")
    oracle_price_stars: int = Field(default=150, alias="ORACLE_PRICE_STARS")

    free_daily_questions: int = Field(default=5, alias="FREE_DAILY_QUESTIONS")

    @property
    def webhook_path(self) -> str:
        return f"/webhook/{self.webhook_secret}"

    @property
    def full_webhook_url(self) -> Optional[str]:
        if not self.webhook_url:
            return None
        return self.webhook_url.rstrip("/") + self.webhook_path

    @property
    def webapp_url(self) -> Optional[str]:
        if not self.webhook_url:
            return None
        return self.webhook_url.rstrip("/") + "/app"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
