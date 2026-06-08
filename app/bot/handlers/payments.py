from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import stars_invoice_price
from app.config import get_settings
from app.database import crud

router = Router(name=__name__)
settings = get_settings()


@router.callback_query(F.data.in_({"buy_pro", "buy_oracle"}))
async def buy_plan(callback_query: CallbackQuery) -> None:
    if callback_query.from_user is None:
        return
    is_pro = callback_query.data == "buy_pro"
    payload = "stellarium_pro_monthly" if is_pro else "stellarium_oracle_monthly"
    title = "Stellarium Pro — месячная подписка" if is_pro else "Космический Оракул — месячная подписка"
    description = (
        "Подробные прогнозы, weekly/monthly, безлимитные вопросы"
        if is_pro
        else "Все из Pro + бизнес-астрология и годовой фокус"
    )
    amount = settings.pro_plan_stars if is_pro else settings.oracle_plan_stars
    label = "Stellarium Pro" if is_pro else "Космический Оракул"
    await callback_query.message.answer_invoice(
        title=title,
        description=description,
        payload=payload,
        currency="XTR",
        prices=stars_invoice_price(amount, label),
        provider_token="",
    )
    await callback_query.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, session: AsyncSession) -> None:
    if message.from_user is None or message.successful_payment is None:
        return
    payload = message.successful_payment.invoice_payload
    if payload == "stellarium_pro_monthly":
        plan = "pro"
        amount = settings.pro_plan_stars
    else:
        plan = "oracle"
        amount = settings.oracle_plan_stars
    await crud.activate_subscription(session, message.from_user.id, plan, amount, months=1)
    await message.answer(
        "✅ Оплата прошла успешно!\n"
        f"Подписка <b>{plan}</b> активирована на 30 дней. Спасибо за поддержку Stellarium AI."
    )
