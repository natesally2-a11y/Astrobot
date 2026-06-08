from __future__ import annotations

from app.astrology.calculations import ChartData
from app.services.subscriptions import FREE_PLAN, ORACLE_PLAN, PLANS, PRO_PLAN


def welcome_text(first_name: str | None = None) -> str:
    name = first_name or "друг"
    return (
        f"👋 Добро пожаловать в Stellarium AI, {name}!\n\n"
        "Я — ваш персональный ИИ-астролог. Создам точную натальную карту и буду "
        "давать прогнозы, основанные именно на вашей карте, а не на общих "
        "гороскопах.\n\n"
        "Для начала мне нужны данные рождения:\n"
        "📅 Дата рождения\n"
        "⏰ Время рождения (хотя бы примерное)\n"
        "📍 Место рождения (город)"
    )


def chart_preview_text(chart: ChartData) -> str:
    top_planets = ", ".join(
        f"{planet.name} в {planet.sign}" for planet in chart.planets[:4]
    )
    return (
        f"✨ Ваша карта готова!\n\n"
        f"{chart.summary}\n\n"
        f"Ключевые акценты: {top_planets}.\n"
        "Команды: /chart, /today, /ask, /settings"
    )


def help_text() -> str:
    return (
        "Доступные команды:\n"
        "/start — приветствие и регистрация\n"
        "/chart — показать натальную карту\n"
        "/today — персональный прогноз на сегодня\n"
        "/week — прогноз на неделю (Premium)\n"
        "/compatibility — совместимость с партнером\n"
        "/ask — задать вопрос астрологу\n"
        "/transit — важные транзиты (Premium)\n"
        "/settings — настройки и подписка\n"
        "/privacy — политика конфиденциальности\n"
        "/my_data — показать сохраненные данные\n"
        "/export_data — экспорт данных в JSON\n"
        "/delete_data — удалить аккаунт и данные\n"
        "/help — справка"
    )


def subscription_short_label(plan_code: str) -> str:
    plan = PLANS.get(plan_code, FREE_PLAN)
    return f"{plan.title} ({plan.price_label})"


def refund_policy_text() -> str:
    return (
        "Подписки оплачиваются через Telegram Stars. Возвраты и отмена продления "
        "оформляются в соответствии с правилами Telegram для Stars; пользователь "
        "должен видеть это до покупки."
    )


def premium_gate_text() -> str:
    return (
        f"Эта функция доступна в {PRO_PLAN.title} и {ORACLE_PLAN.title}. "
        "Откройте /settings, чтобы оформить подписку через Telegram Stars."
    )
