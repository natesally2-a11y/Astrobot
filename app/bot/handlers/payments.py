"""Telegram Stars payments handler."""

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    PreCheckoutQuery,
    LabeledPrice,
)

from app.database.crud import create_subscription, check_subscription_level
from app.bot.keyboards.inline import subscription_keyboard
from app.config import settings

router = Router()

PLANS = {
    "pro": {
        "title": "Stellarium Pro — месячная подписка",
        "description": (
            "Подробные ежедневные прогнозы, недельные и месячные прогнозы, "
            "анализ совместимости и безлимитные вопросы ИИ"
        ),
        "payload": "stellarium_pro_monthly",
        "amount": settings.pro_stars_price,
        "plan_type": "pro",
    },
    "oracle": {
        "title": "Космический Оракул — месячная подписка",
        "description": (
            "Всё из Pro + бизнес-астрология, годовые прогнозы, "
            "индивидуальные ритуалы и приоритетная поддержка ИИ"
        ),
        "payload": "stellarium_oracle_monthly",
        "amount": settings.oracle_stars_price,
        "plan_type": "oracle",
    },
}


@router.callback_query(F.data.startswith("subscribe_"))
async def subscribe(callback: CallbackQuery):
    plan_key = callback.data.replace("subscribe_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        await callback.answer("План не найден", show_alert=True)
        return

    level = await check_subscription_level(callback.from_user.id)
    if level == plan["plan_type"]:
        await callback.answer("У вас уже есть эта подписка!", show_alert=True)
        return

    await callback.message.answer_invoice(
        title=plan["title"],
        description=plan["description"],
        payload=plan["payload"],
        currency="XTR",
        prices=[LabeledPrice(label=plan["title"], amount=plan["amount"])],
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    if not message.from_user or not message.successful_payment:
        return

    payment = message.successful_payment
    payload = payment.invoice_payload

    plan = None
    for p in PLANS.values():
        if p["payload"] == payload:
            plan = p
            break

    if not plan:
        await message.answer("⚠️ Ошибка обработки платежа. Обратитесь в поддержку.")
        return

    await create_subscription(
        user_id=message.from_user.id,
        plan_type=plan["plan_type"],
        stars_amount=plan["amount"],
        days=30,
        telegram_charge_id=payment.telegram_payment_charge_id,
    )

    plan_names = {"pro": "Stellarium Pro ⭐", "oracle": "Космический Оракул 🔮"}
    await message.answer(
        f"🎉 <b>Подписка активирована!</b>\n\n"
        f"План: {plan_names.get(plan['plan_type'], plan['plan_type'])}\n"
        f"Срок: 30 дней\n\n"
        f"Теперь вам доступны все возможности подписки.\n"
        f"Попробуйте /today для подробного прогноза!",
        parse_mode="HTML",
    )
