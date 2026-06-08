"""Subscription plans for Telegram Stars (XTR) payments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class Plan:
    code: str
    title: str
    description: str
    stars: int               # amount in Telegram Stars (XTR)
    price_rub: int           # nominal RUB price for display
    duration_days: int = 30
    payload: str = ""
    perks: tuple[str, ...] = ()

    def to_invoice_kwargs(self) -> dict:
        return dict(
            title=self.title,
            description=self.description,
            payload=self.payload or self.code,
            currency="XTR",
            prices=[{"label": self.title, "amount": self.stars}],
        )


PLANS: Dict[str, Plan] = {
    "pro": Plan(
        code="pro",
        title="Stellarium Pro — месячная подписка",
        description=(
            "Подробные дневные и недельные прогнозы, безлимитные вопросы ИИ, "
            "анализ совместимости до 3 партнёров и уведомления о транзитах."
        ),
        stars=50,
        price_rub=99,
        payload="stellarium_pro_monthly",
        perks=(
            "Подробные ежедневные и недельные прогнозы",
            "Анализ совместимости (до 3 партнёров)",
            "Безлимитные вопросы ИИ",
            "Уведомления о важных транзитах",
        ),
    ),
    "oracle": Plan(
        code="oracle",
        title="Космический Оракул — месячная подписка",
        description=(
            "Всё из Pro плюс бизнес-астрология, годовые прогнозы, индивидуальные "
            "ритуалы и приоритетный ИИ."
        ),
        stars=150,
        price_rub=299,
        payload="stellarium_oracle_monthly",
        perks=(
            "Всё из Pro",
            "Бизнес-астрология (благоприятные даты)",
            "Годовые прогнозы (солнечные возвращения)",
            "Индивидуальные ритуалы и рекомендации",
            "Приоритетная поддержка ИИ",
        ),
    ),
}


def get_plan(code: str) -> Optional[Plan]:
    return PLANS.get(code)
