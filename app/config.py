from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Stellarium AI"
    app_base_url: str = "http://localhost:8000"
    webapp_path: str = "/app"

    bot_token: str = Field(default="replace-with-bot-token", alias="BOT_TOKEN")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    database_url: str = Field(
        default="postgresql+asyncpg://stellarium:stellarium@db:5432/stellarium",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    run_bot_polling: bool = Field(default=True, alias="RUN_BOT_POLLING")
    free_daily_question_limit: int = Field(default=5, alias="FREE_DAILY_QUESTION_LIMIT")

    pro_monthly_stars: int = Field(default=50, alias="PRO_MONTHLY_STARS")
    oracle_monthly_stars: int = Field(default=150, alias="ORACLE_MONTHLY_STARS")

    @property
    def webapp_url(self) -> str:
        return f"{self.app_base_url.rstrip('/')}{self.webapp_path}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

