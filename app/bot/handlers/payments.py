from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import crud

router = Router()
settings = get_settings()

PLANS = {
    "subscribe_pro": ("pro", settings.pro_stars, "Stellarium Pro — месячная подписка"),
    "subscribe_oracle": ("oracle", settings.oracle_stars, "Космический Оракул — месячная подписка"),
}


@router.callback_query(F.data.in_({"subscribe_pro", "subscribe_oracle"}))
async def send_invoice(callback: CallbackQuery) -> None:
    plan_type, stars, title = PLANS[callback.data]
    await callback.message.answer_invoice(
        title=title,
        description="Персональные прогнозы и безлимитный ИИ-астролог",
        payload=f"stellarium_{plan_type}_monthly",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=stars)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, session: AsyncSession) -> None:
    payment = message.successful_payment
    payload = payment.invoice_payload

    plan_map = {
        "stellarium_pro_monthly": ("pro", settings.pro_stars),
        "stellarium_oracle_monthly": ("oracle", settings.oracle_stars),
    }
    plan_info = plan_map.get(payload)
    if not plan_info:
        await message.answer("❌ Неизвестный платёж. Обратитесь в поддержку.")
        return

    plan_type, stars = plan_info
    user = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )
    await crud.activate_subscription(session, user, plan_type, stars)

    plan_names = {"pro": "⭐ Stellarium Pro", "oracle": "🌌 Космический Оракул"}
    await message.answer(
        f"✅ Подписка {plan_names[plan_type]} активирована!\n"
        f"Спасибо за оплату {stars} Stars.\n\n"
        f"Возврат: обратитесь в поддержку Telegram в течение 7 дней."
    )
