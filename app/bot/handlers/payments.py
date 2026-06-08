from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.config import get_settings
from app.database.crud import upsert_subscription
from app.database.session import AsyncSessionLocal

router = Router(name="payments")
settings = get_settings()

PLANS = {
    "pro": {
        "title": "Stellarium Pro — месячная подписка",
        "description": "Персональные прогнозы, weekly, transit и безлимитные вопросы",
        "payload": "stellarium_pro_monthly",
        "stars": settings.pro_monthly_stars,
        "plan_type": "pro",
    },
    "oracle": {
        "title": "Космический Оракул — месячная подписка",
        "description": "Расширенные прогнозы, ритуалы и приоритетная поддержка",
        "payload": "stellarium_oracle_monthly",
        "stars": settings.oracle_monthly_stars,
        "plan_type": "oracle",
    },
}


@router.callback_query(F.data.startswith("buy:"))
async def buy_subscription(callback: CallbackQuery) -> None:
    _, plan_key = callback.data.split(":")
    plan = PLANS.get(plan_key)
    if not plan:
        await callback.answer("План не найден", show_alert=True)
        return

    await callback.message.answer_invoice(
        title=plan["title"],
        description=plan["description"],
        payload=plan["payload"],
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=plan["title"], amount=plan["stars"])],
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payload = message.successful_payment.invoice_payload
    if payload == "stellarium_pro_monthly":
        plan_type = "pro"
        stars = settings.pro_monthly_stars
    elif payload == "stellarium_oracle_monthly":
        plan_type = "oracle"
        stars = settings.oracle_monthly_stars
    else:
        await message.answer("Платеж получен, но план не распознан. Напишите в поддержку.")
        return

    async with AsyncSessionLocal() as session:
        await upsert_subscription(
            session=session,
            user_id=message.from_user.id,
            plan_type=plan_type,
            stars_amount=stars,
            duration_days=30,
        )

    await message.answer("✅ Подписка активирована. Спасибо за поддержку Stellarium AI!")

