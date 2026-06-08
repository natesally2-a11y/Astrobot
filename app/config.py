from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    webhook_url: str = Field("", alias="WEBHOOK_URL")
    webhook_path: str = Field("/webhook", alias="WEBHOOK_PATH")

    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", alias="OPENAI_MODEL")

    database_url: str = Field(
        "postgresql+asyncpg://stellarium:stellarium@localhost:5432/stellarium",
        alias="DATABASE_URL",
    )
    redis_url: str = Field("redis://localhost:6379", alias="REDIS_URL")

    secret_key: str = Field("change-me-in-production", alias="SECRET_KEY")

    webapp_url: str = Field("", alias="WEBAPP_URL")

    free_daily_questions: int = 5
    pro_stars_price: int = 50
    oracle_stars_price: int = 150
    pro_monthly_days: int = 30
    oracle_monthly_days: int = 30

    nominatim_user_agent: str = "stellarium-ai-bot/1.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


settings = Settings()
