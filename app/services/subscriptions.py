from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.crud import count_daily_questions, get_active_subscription
from app.database.models import User


settings = get_settings()


@dataclass(slots=True)
class Plan:
    code: str
    title: str
    stars: int
    price_label: str
    features: tuple[str, ...]


FREE_PLAN = Plan(
    code="free",
    title="Free",
    stars=0,
    price_label="0₽",
    features=(
        "Натальная карта",
        "Базовый анализ личности",
        "Краткий прогноз на сегодня",
        "5 вопросов ИИ в день",
    ),
)
PRO_PLAN = Plan(
    code="pro",
    title="Stellarium Pro",
    stars=settings.pro_plan_stars,
    price_label="99₽ / ~50 Stars",
    features=(
        "Подробные ежедневные прогнозы",
        "Недельные прогнозы",
        "Совместимость до 3 партнеров",
        "Безлимитные вопросы ИИ",
        "Уведомления о транзитах",
    ),
)
ORACLE_PLAN = Plan(
    code="oracle",
    title="Cosmic Oracle",
    stars=settings.oracle_plan_stars,
    price_label="299₽ / ~150 Stars",
    features=(
        "Все возможности Pro",
        "Бизнес-астрология и благоприятные даты",
        "Годовые прогнозы",
        "Индивидуальные ритуалы",
        "Приоритетная поддержка",
    ),
)

PLANS = {plan.code: plan for plan in (FREE_PLAN, PRO_PLAN, ORACLE_PLAN)}


async def resolve_user_tier(session: AsyncSession, user: User | None) -> str:
    if not user:
        return FREE_PLAN.code

    active = await get_active_subscription(session, user.telegram_id)
    if active and active.expires_at > datetime.utcnow():
        return active.plan_type
    return FREE_PLAN.code


async def can_ask_question(session: AsyncSession, user: User | None) -> tuple[bool, int]:
    tier = await resolve_user_tier(session, user)
    if tier in {PRO_PLAN.code, ORACLE_PLAN.code}:
        return True, -1

    if not user:
        return False, settings.free_daily_questions_limit

    used = await count_daily_questions(session, user.telegram_id)
    remaining = max(settings.free_daily_questions_limit - used, 0)
    return remaining > 0, remaining


def plan_summary_text(current_plan: str) -> str:
    lines = []
    for plan in (FREE_PLAN, PRO_PLAN, ORACLE_PLAN):
        prefix = "✅" if plan.code == current_plan else "•"
        features = "\n   ".join(plan.features)
        lines.append(f"{prefix} {plan.title} — {plan.price_label}\n   {features}")
    lines.append(
        "\nПодписки оплачиваются через Telegram Stars. Возвраты оформляются "
        "по правилам Telegram и должны быть описаны пользователю прозрачно до покупки."
    )
    return "\n\n".join(lines)
