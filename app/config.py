"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed settings backed by environment variables / .env file."""

    # --- Telegram ---
    bot_token: str = Field(..., alias="BOT_TOKEN")
    bot_username: str = Field("StellariumAIBot", alias="BOT_USERNAME")
    webhook_url: Optional[str] = Field(None, alias="WEBHOOK_URL")
    webhook_path: str = Field("/webhook", alias="WEBHOOK_PATH")
    webhook_secret: str = Field("stellarium-webhook-secret", alias="WEBHOOK_SECRET")

    # --- Web / Mini App ---
    app_host: str = Field("0.0.0.0", alias="APP_HOST")
    app_port: int = Field(8000, alias="APP_PORT")
    webapp_public_url: str = Field("https://example.com", alias="WEBAPP_PUBLIC_URL")

    # --- OpenAI ---
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o-mini", alias="OPENAI_MODEL")

    # --- Database ---
    database_url: str = Field(
        "sqlite+aiosqlite:///./stellarium.db", alias="DATABASE_URL"
    )

    # --- Redis ---
    redis_url: Optional[str] = Field(None, alias="REDIS_URL")

    # --- Security ---
    secret_key: str = Field("change-me", alias="SECRET_KEY")

    # --- Swiss Ephemeris ---
    swe_ephe_path: Optional[str] = Field(None, alias="SWE_EPHE_PATH")

    # --- Misc ---
    default_language: str = Field("ru", alias="DEFAULT_LANGUAGE")
    admin_ids_raw: str = Field("", alias="ADMIN_IDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def admin_ids(self) -> List[int]:
        if not self.admin_ids_raw:
            return []
        return [
            int(x.strip())
            for x in self.admin_ids_raw.split(",")
            if x.strip().lstrip("-").isdigit()
        ]

    # --- Derived properties ---
    @property
    def use_webhook(self) -> bool:
        return bool(self.webhook_url)

    @property
    def mini_app_url(self) -> str:
        return f"{self.webapp_public_url.rstrip('/')}/app"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor."""
    return Settings()  # type: ignore[call-arg]
