"""Subscription plan definitions and pricing (Telegram Stars)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from app.database.models import PLAN_ORACLE, PLAN_PRO


@dataclass(frozen=True)
class Plan:
    code: str
    title: str
    price_rub: int
    stars: int
    payload: str
    duration_days: int
    features: List[str] = field(default_factory=list)


PLANS: Dict[str, Plan] = {
    PLAN_PRO: Plan(
        code=PLAN_PRO,
        title="Stellarium Pro",
        price_rub=99,
        stars=50,
        payload="stellarium_pro_monthly",
        duration_days=30,
        features=[
            "Подробные ежедневные прогнозы",
            "Недельные и месячные прогнозы",
            "Анализ совместимости (до 3 партнёров)",
            "Безлимитные вопросы ИИ",
            "Уведомления о важных транзитах",
        ],
    ),
    PLAN_ORACLE: Plan(
        code=PLAN_ORACLE,
        title="Космический Оракул",
        price_rub=299,
        stars=150,
        payload="stellarium_oracle_monthly",
        duration_days=30,
        features=[
            "Всё из Pro",
            "Бизнес-астрология (благоприятные даты)",
            "Годовые прогнозы (солнечные возвращения)",
            "Индивидуальные ритуалы и рекомендации",
            "Приоритетная поддержка ИИ",
        ],
    ),
}

PLAN_BY_PAYLOAD = {p.payload: p for p in PLANS.values()}

# Which features require which minimum plan.
PREMIUM_PLANS = {PLAN_PRO, PLAN_ORACLE}


def plan_features_text(plan: Plan) -> str:
    bullets = "\n".join(f"• {f}" for f in plan.features)
    return (
        f"*{plan.title}* — {plan.price_rub}₽/мес (≈{plan.stars} ⭐)\n{bullets}"
    )
