"""Подписки через Telegram Stars (XTR)."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import crud
from app.plans import ORACLE, PRO, get_plan, plan_by_payload

logger = logging.getLogger(__name__)
router = Router(name="payments")


async def _send_invoice(call: CallbackQuery, plan_code: str) -> None:
    plan = get_plan(plan_code)
    await call.message.answer_invoice(
        title=f"{plan.title} — месячная подписка",
        description="Персональные прогнозы и безлимитный ИИ-астролог Stellarium AI",
        payload=plan.payload,
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=plan.title, amount=plan.stars)],
        # provider_token не требуется для оплаты звёздами
    )
    await call.answer()


@router.callback_query(F.data == "buy:pro")
async def buy_pro(call: CallbackQuery) -> None:
    await _send_invoice(call, PRO)


@router.callback_query(F.data == "buy:oracle")
async def buy_oracle(call: CallbackQuery) -> None:
    await _send_invoice(call, ORACLE)


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    plan = plan_by_payload(query.invoice_payload)
    if plan is None:
        await query.answer(ok=False, error_message="Неизвестный тариф")
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, session: AsyncSession) -> None:
    sp = message.successful_payment
    plan = plan_by_payload(sp.invoice_payload)
    if plan is None:
        logger.warning("Unknown payload in payment: %s", sp.invoice_payload)
        return

    await crud.activate_subscription(
        session,
        telegram_id=message.from_user.id,
        plan_code=plan.code,
        stars_amount=sp.total_amount,
        duration_days=plan.duration_days,
        telegram_charge_id=sp.telegram_payment_charge_id,
    )
    await message.answer(
        f"✅ Оплата прошла успешно! Подписка <b>{plan.title}</b> активирована "
        f"на {plan.duration_days} дней.\n\nСпасибо, что выбрали Stellarium AI ✨"
    )
