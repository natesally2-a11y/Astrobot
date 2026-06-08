"""Конфигурация приложения на основе переменных окружения."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Все настройки читаются из переменных окружения / файла .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Telegram
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    bot_username: str = Field(default="stellarium_ai_bot", alias="BOT_USERNAME")
    webhook_base_url: str = Field(default="", alias="WEBHOOK_BASE_URL")
    webhook_secret: str = Field(default="change-me", alias="WEBHOOK_SECRET")
    bot_mode: str = Field(default="polling", alias="BOT_MODE")  # polling | webhook

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")

    # Database / cache
    database_url: str = Field(
        default="postgresql+asyncpg://stellarium:stellarium@db:5432/stellarium",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # Security
    secret_key: str = Field(default="change-me-secret-key", alias="SECRET_KEY")

    # Misc
    privacy_contact_email: str = Field(
        default="privacy@example.com", alias="PRIVACY_CONTACT_EMAIL"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def webhook_path(self) -> str:
        return "/webhook"

    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"

    @property
    def webapp_url(self) -> str:
        return f"{self.webhook_base_url.rstrip('/')}/app"

    @property
    def use_webhook(self) -> bool:
        return self.bot_mode.lower() == "webhook"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
