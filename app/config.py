from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DISCLAIMER_TEXT = (
    "⚠️ Важно: Астрологические прогнозы носят исключительно развлекательный "
    "характер и не являются руководством к действию.\n\n"
    "Не используйте астрологию для принятия важных жизненных, медицинских "
    "или финансовых решений. При серьезных проблемах обращайтесь к "
    "квалифицированным специалистам.\n\n"
    "Stellarium AI создан для саморазвития и развлечения."
)

GDPR_CONSENT_TEXT = (
    "📋 Согласие на обработку персональных данных\n\n"
    "Для создания персональной натальной карты нам необходимы:\n"
    "• Дата, время и место рождения\n"
    "• Имя для персонализации\n\n"
    "Мы обрабатываем эти данные для:\n"
    "✅ Астрологических расчетов\n"
    "✅ Персонализированных прогнозов\n"
    "✅ Работы подписки\n\n"
    "Мы НЕ передаем данные третьим лицам.\n"
    "Вы можете удалить все данные командой /delete_data\n\n"
    "Нажимая кнопку «Согласен», вы подтверждаете согласие с обработкой "
    "данных в соответствии с ФЗ-152 и GDPR."
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Stellarium AI"
    app_env: Literal["local", "dev", "prod"] = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    base_url: str = "http://localhost:8000"
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret used to sign internal webapp sessions.",
    )

    bot_token: str = Field(default="", alias="BOT_TOKEN")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_path: str = "/webhook"

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4.1-mini"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./stellarium.db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    pro_plan_stars: int = 50
    oracle_plan_stars: int = 150
    free_daily_questions_limit: int = 5

    support_email: str = "privacy@stellarium.ai"
    privacy_policy_url: str = "https://example.com/privacy"
    terms_url: str = "https://example.com/terms"

    sample_birth_place: str = "Moscow, Russia"
    sample_birth_date: str = "1994-11-17"
    sample_birth_time: str = "09:30"

    def webhook_full_url(self) -> str:
        if not self.webhook_url:
            return ""
        return f"{self.webhook_url.rstrip('/')}{self.webhook_path}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
