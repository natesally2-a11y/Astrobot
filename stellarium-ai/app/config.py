from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    BOT_TOKEN: str = "8730150448:AAF2WIWbalTieFVb2lc1kdtGIAkrtflgLvs"
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stellarium"
    REDIS_URL: str = "redis://localhost:6379"

    SECRET_KEY: str = "stellarium-secret-key-change-in-production"

    # Subscription prices in Telegram Stars
    PRO_PRICE_STARS: int = 50        # ~99 RUB
    ORACLE_PRICE_STARS: int = 150     # ~299 RUB

    # Free tier limits
    FREE_QUESTIONS_PER_DAY: int = 5

    # App settings
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Referral bonus (days of Pro)
    REFERRAL_BONUS_DAYS: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
