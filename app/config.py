from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "staging", "production"] = "development"

    bot_token: SecretStr = Field(..., alias="BOT_TOKEN")
    webhook_url: AnyUrl | None = Field(default=None, alias="WEBHOOK_URL")
    webapp_url: AnyUrl | None = Field(default=None, alias="WEBAPP_URL")
    bot_username: str = Field(default="stellarium_ai_bot", alias="BOT_USERNAME")

    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")

    database_url: str = Field(
        default="postgresql+asyncpg://stellarium:stellarium@localhost:5432/stellarium",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    secret_key: SecretStr = Field(default=SecretStr("change-me"), alias="SECRET_KEY")

    @field_validator("webhook_url", "webapp_url", mode="before")
    @classmethod
    def empty_url_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return self.database_url

    @property
    def safe_webapp_url(self) -> str:
        return str(self.webapp_url or "https://example.com/app")


@lru_cache
def get_settings() -> Settings:
    return Settings()
