"""Тарифные планы и лимиты подписок Stellarium AI."""
from __future__ import annotations

from dataclasses import dataclass, field


FREE = "free"
PRO = "pro"
ORACLE = "oracle"


@dataclass(frozen=True)
class Plan:
    code: str
    title: str
    price_rub: int
    stars: int  # стоимость в Telegram Stars (XTR), 0 для free
    daily_ask_limit: int  # -1 = безлимит
    duration_days: int
    payload: str
    features: list[str] = field(default_factory=list)

    @property
    def is_paid(self) -> bool:
        return self.stars > 0


PLANS: dict[str, Plan] = {
    FREE: Plan(
        code=FREE,
        title="Бесплатный",
        price_rub=0,
        stars=0,
        daily_ask_limit=5,
        duration_days=0,
        payload="stellarium_free",
        features=[
            "Создание натальной карты",
            "Базовый анализ личности",
            "Краткий ежедневный прогноз",
            "5 вопросов ИИ в день",
        ],
    ),
    PRO: Plan(
        code=PRO,
        title="Stellarium Pro",
        price_rub=99,
        stars=50,
        daily_ask_limit=-1,
        duration_days=30,
        payload="stellarium_pro_monthly",
        features=[
            "Подробные ежедневные прогнозы",
            "Недельные и месячные прогнозы",
            "Анализ совместимости (до 3 партнёров)",
            "Безлимитные вопросы ИИ",
            "Уведомления о важных транзитах",
        ],
    ),
    ORACLE: Plan(
        code=ORACLE,
        title="Космический Оракул",
        price_rub=299,
        stars=150,
        daily_ask_limit=-1,
        duration_days=30,
        payload="stellarium_oracle_monthly",
        features=[
            "Всё из Pro",
            "Бизнес-астрология (благоприятные даты)",
            "Годовые прогнозы (солнечные возвращения)",
            "Индивидуальные ритуалы и рекомендации",
            "Приоритетная поддержка ИИ",
        ],
    ),
}


def get_plan(code: str) -> Plan:
    return PLANS.get(code, PLANS[FREE])


def plan_by_payload(payload: str) -> Plan | None:
    for plan in PLANS.values():
        if plan.payload == payload:
            return plan
    return None


# Уровни доступа: какие планы дают премиум-функции
PREMIUM_PLANS = {PRO, ORACLE}


def is_premium(code: str) -> bool:
    return code in PREMIUM_PLANS
