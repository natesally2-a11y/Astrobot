from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Stellarium AI'
    app_base_url: str = 'http://localhost:8000'
    bot_token: str = ''
    webhook_url: str = ''

    openai_api_key: str = ''
    openai_model: str = 'gpt-4.1-mini'

    database_url: str = 'sqlite+aiosqlite:///./stellarium.db'
    redis_url: str = 'redis://localhost:6379/0'
    secret_key: str = 'change-me'

    default_timezone: str = 'Europe/Moscow'
    nominatim_user_agent: str = 'stellarium-ai-bot/1.0'
    enable_demo_data: bool = True

    free_daily_questions: int = 5
    pro_plan_stars: int = 50
    oracle_plan_stars: int = 150
    pro_plan_rub: int = 99
    oracle_plan_rub: int = 299

    default_language: Literal['ru', 'en'] = 'ru'

    @computed_field
    @property
    def webapp_url(self) -> str:
        return f'{self.app_base_url.rstrip("/")}/app'


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
