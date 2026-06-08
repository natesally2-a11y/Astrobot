from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(default="123456:REPLACE_WITH_REAL_BOT_TOKEN", alias="BOT_TOKEN")
    webhook_url: str | None = Field(default=None, alias="WEBHOOK_URL")
    webapp_base_url: str | None = Field(default=None, alias="WEBAPP_BASE_URL")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    database_url: str = Field(
        default="postgresql+asyncpg://stellarium:stellarium@db:5432/stellarium",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")

    pro_plan_stars: int = Field(default=50, alias="PRO_PLAN_STARS")
    oracle_plan_stars: int = Field(default=150, alias="ORACLE_PLAN_STARS")
    free_daily_questions: int = Field(default=5, alias="FREE_DAILY_QUESTIONS")

    nominatim_url: str = Field(
        default="https://nominatim.openstreetmap.org/search",
        alias="NOMINATIM_URL",
    )
    nominatim_user_agent: str = Field(default="stellarium-ai-bot", alias="NOMINATIM_USER_AGENT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
