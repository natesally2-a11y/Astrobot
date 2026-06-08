"""
Telegram Stars payment handlers.
"""
from __future__ import annotations

from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
)

from app.database import crud
from app.database.models import User
from app.bot.keyboards.inline import SubscriptionCD, get_main_menu_keyboard
from app.config import settings

router = Router(name="payments")

PLANS = {
    "pro": {
        "title": "Stellarium Pro — Месячная подписка",
        "description": "Полные прогнозы, безлимитные вопросы ИИ, анализ совместимости, уведомления о транзитах",
        "stars": settings.PRO_PRICE_STARS,
        "label": "Stellarium Pro (1 месяц)",
        "payload": "stellarium_pro_monthly",
    },
    "oracle": {
        "title": "Космический Оракул — Месячная подписка",
        "description": "Всё из Pro + бизнес-астрология, годовые прогнозы, индивидуальные ритуалы и приоритетная поддержка",
        "stars": settings.ORACLE_PRICE_STARS,
        "label": "Космический Оракул (1 месяц)",
        "payload": "stellarium_oracle_monthly",
    },
}


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    from app.bot.keyboards.inline import get_subscription_keyboard
    await message.answer(
        "⭐ <b>Выберите тарифный план</b>\n\n"
        "🆓 <b>Бесплатно:</b>\n"
        "• Натальная карта\n"
        "• Базовый анализ личности\n"
        "• Ежедневный прогноз (краткий)\n"
        f"• {settings.FREE_QUESTIONS_PER_DAY} вопросов в день\n\n"
        "⭐ <b>Stellarium Pro — 50 Stars/мес (~99₽):</b>\n"
        "• Подробные ежедневные прогнозы\n"
        "• Недельные и месячные прогнозы\n"
        "• Анализ совместимости (до 3 партнёров)\n"
        "• Безлимитные вопросы ИИ\n"
        "• Уведомления о важных транзитах\n\n"
        "🔮 <b>Космический Оракул — 150 Stars/мес (~299₽):</b>\n"
        "• Всё из Pro +\n"
        "• Бизнес-астрология\n"
        "• Годовые прогнозы\n"
        "• Индивидуальные ритуалы\n"
        "• Приоритетная поддержка ИИ",
        parse_mode="HTML",
        reply_markup=__import__(
            "app.bot.keyboards.inline", fromlist=["get_subscription_keyboard"]
        ).get_subscription_keyboard(),
    )


@router.callback_query(SubscriptionCD.filter())
async def subscription_callback(
    callback: CallbackQuery, callback_data: SubscriptionCD, session=None
):
    await callback.answer()
    plan = callback_data.plan
    if plan not in PLANS:
        return
    await send_invoice_for_plan(callback.message, plan)


@router.callback_query(F.data == "sub:cancel")
async def cancel_subscription(callback: CallbackQuery):
    await callback.answer("Отменено")
    await callback.message.delete()


async def send_invoice_for_plan(message: Message, plan: str):
    if plan not in PLANS:
        return

    plan_data = PLANS[plan]
    await message.answer_invoice(
        title=plan_data["title"],
        description=plan_data["description"],
        payload=plan_data["payload"],
        currency="XTR",
        prices=[LabeledPrice(label=plan_data["label"], amount=plan_data["stars"])],
    )


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    payload = pre_checkout_query.invoice_payload
    if payload in ("stellarium_pro_monthly", "stellarium_oracle_monthly"):
        await pre_checkout_query.answer(ok=True)
    else:
        await pre_checkout_query.answer(ok=False, error_message="Неверный платёж.")


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, session=None, db_user: Optional[User] = None):
    payment = message.successful_payment
    payload = payment.invoice_payload
    stars = payment.total_amount
    payment_id = payment.telegram_payment_charge_id
    user_id = message.from_user.id

    if payload == "stellarium_pro_monthly":
        plan = "pro"
    elif payload == "stellarium_oracle_monthly":
        plan = "oracle"
    else:
        return

    if session:
        await crud.activate_subscription(
            session, user_id, plan, stars, payment_id
        )

    plan_names = {"pro": "Stellarium Pro ⭐", "oracle": "Космический Оракул 🔮"}
    await message.answer(
        f"🎉 <b>Подписка активирована!</b>\n\n"
        f"✅ {plan_names.get(plan, plan)}\n"
        f"💎 Оплачено: {stars} Telegram Stars\n\n"
        f"Добро пожаловать в мир персональной астрологии!\n"
        f"Используйте /chart, /today, /week и /transit.",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(has_birth_data=True, is_pro=True),
    )
