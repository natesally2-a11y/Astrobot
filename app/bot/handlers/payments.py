"""Telegram Stars payment callbacks (pre-checkout & successful payment)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import add_subscription
from app.database.models import User
from app.payments import PLANS

router = Router(name="payments")


_PAYLOAD_TO_PLAN = {plan.payload: plan for plan in PLANS.values()}


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    plan = _PAYLOAD_TO_PLAN.get(query.invoice_payload)
    if plan is None:
        await query.answer(ok=False, error_message="Неизвестный план подписки.")
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(
    message: Message, session: AsyncSession, user: User
) -> None:
    payment = message.successful_payment
    plan = _PAYLOAD_TO_PLAN.get(payment.invoice_payload)
    if plan is None:
        await message.answer("Платёж получен, но план не распознан. Напишите в поддержку.")
        return

    await add_subscription(
        session,
        user_id=user.telegram_id,
        plan_type=plan.code,
        stars_amount=payment.total_amount,
        duration_days=plan.duration_days,
        telegram_payment_charge_id=payment.telegram_payment_charge_id,
    )
    await message.answer(
        f"🎉 Подписка <b>{plan.title.split(' — ')[0]}</b> активирована на "
        f"{plan.duration_days} дней!\n\n"
        "Доступ к Premium-функциям открыт. /menu",
        parse_mode="HTML",
    )
