from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = ""
    webhook_url: str = ""
    webapp_url: str = "http://localhost:8000/app"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    database_url: str = "postgresql+asyncpg://stellarium:stellarium@localhost:5432/stellarium"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "change-me"

    debug: bool = False
    free_daily_questions: int = 5
    pro_stars: int = 50
    oracle_stars: int = 150

    @property
    def webhook_path(self) -> str:
        return "/webhook"

    @property
    def full_webhook_url(self) -> str:
        return f"{self.webhook_url.rstrip('/')}{self.webhook_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
