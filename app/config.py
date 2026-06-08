from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: SecretStr | None = Field(default=None, alias="BOT_TOKEN")
    webhook_url: str | None = Field(default=None, alias="WEBHOOK_URL")
    webapp_url: str | None = Field(default=None, alias="WEBAPP_URL")
    bot_username: str = Field(default="stellarium_ai_bot", alias="BOT_USERNAME")

    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")

    database_url: str = Field(
        default="postgresql+asyncpg://stellarium:stellarium@localhost:5432/stellarium",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"), alias="SECRET_KEY")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    nominatim_user_agent: str = Field(
        default="StellariumAI/1.0 (development@example.com)",
        alias="NOMINATIM_USER_AGENT",
    )

    free_daily_questions: int = Field(default=5, alias="FREE_DAILY_QUESTIONS")
    pro_stars_amount: int = Field(default=50, alias="PRO_STARS_AMOUNT")
    oracle_stars_amount: int = Field(default=150, alias="ORACLE_STARS_AMOUNT")

    def require_bot_token(self) -> str:
        if self.bot_token is None:
            raise RuntimeError("BOT_TOKEN is required to start Telegram bot integration.")
        return self.bot_token.get_secret_value()

    def require_openai_key(self) -> str:
        if self.openai_api_key is None:
            raise RuntimeError("OPENAI_API_KEY is required for live AI interpretations.")
        return self.openai_api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()
