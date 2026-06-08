"""Telegram Stars payments for subscriptions."""
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

from app.bot.keyboards.inline import main_menu_keyboard
from app.bot.plans import PLAN_BY_PAYLOAD, PLANS
from app.database import crud
from app.database.models import PLAN_PRO, PLAN_ORACLE, User

logger = logging.getLogger(__name__)
router = Router(name="payments")

_CODE_BY_BUTTON = {"buy:pro": PLAN_PRO, "buy:oracle": PLAN_ORACLE}


@router.callback_query(F.data.in_(set(_CODE_BY_BUTTON.keys())))
async def cb_buy(callback: CallbackQuery) -> None:
    plan = PLANS[_CODE_BY_BUTTON[callback.data]]
    await callback.message.answer_invoice(
        title=f"{plan.title} — месячная подписка",
        description="Персональные прогнозы и безлимитный ИИ-астролог. "
        f"Подписка на {plan.duration_days} дней.",
        payload=plan.payload,
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=plan.title, amount=plan.stars)],
        # provider_token is intentionally empty for Telegram Stars payments.
    )
    await callback.answer()


@router.pre_checkout_query()
async def on_pre_checkout(pre_checkout: PreCheckoutQuery) -> None:
    # Always approve — validation already happened when building the invoice.
    ok = pre_checkout.invoice_payload in PLAN_BY_PAYLOAD
    await pre_checkout.answer(ok=ok, error_message=None if ok else "Неизвестный тариф")


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, session: AsyncSession, user: User) -> None:
    sp = message.successful_payment
    plan = PLAN_BY_PAYLOAD.get(sp.invoice_payload)
    if not plan:
        logger.warning("Unknown payload in successful payment: %s", sp.invoice_payload)
        return

    await crud.activate_subscription(
        session,
        user_id=user.telegram_id,
        plan_type=plan.code,
        stars_amount=sp.total_amount,
        duration_days=plan.duration_days,
        charge_id=sp.telegram_payment_charge_id,
    )

    await message.answer(
        f"🎉 Оплата получена! Подписка *{plan.title}* активирована на "
        f"{plan.duration_days} дней.\n\nСпасибо, что выбираете Stellarium AI ✨",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
