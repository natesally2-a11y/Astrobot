"""Telegram Stars payment flow."""

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

from app.config import settings
from app.database import crud
from app.database.models import SubscriptionTier, User

logger = logging.getLogger(__name__)
router = Router(name="payments")


PLAN_PAYLOADS = {
    "stellarium_pro_monthly": (SubscriptionTier.PRO, settings.pro_price_stars),
    "stellarium_oracle_monthly": (
        SubscriptionTier.ORACLE,
        settings.oracle_price_stars,
    ),
}


@router.callback_query(F.data == "buy:pro")
async def buy_pro(callback: CallbackQuery) -> None:
    await _send_invoice(
        callback.message,
        title="Stellarium Pro — месячная подписка",
        description=(
            "Подробные прогнозы, анализ совместимости, безлимитные вопросы ИИ."
        ),
        payload="stellarium_pro_monthly",
        amount=settings.pro_price_stars,
    )
    await callback.answer()


@router.callback_query(F.data == "buy:oracle")
async def buy_oracle(callback: CallbackQuery) -> None:
    await _send_invoice(
        callback.message,
        title="Космический Оракул — месячная подписка",
        description=(
            "Всё из Pro плюс годовые прогнозы, бизнес-астрология и"
            " персональные ритуалы."
        ),
        payload="stellarium_oracle_monthly",
        amount=settings.oracle_price_stars,
    )
    await callback.answer()


async def _send_invoice(
    message: Message, *, title: str, description: str, payload: str, amount: int
) -> None:
    await message.answer_invoice(
        title=title,
        description=description,
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=amount)],
        start_parameter=payload,
    )


@router.pre_checkout_query()
async def pre_checkout(pcq: PreCheckoutQuery) -> None:
    if pcq.invoice_payload in PLAN_PAYLOADS:
        await pcq.answer(ok=True)
    else:
        await pcq.answer(ok=False, error_message="Неизвестный товар")


@router.message(F.successful_payment)
async def successful_payment(
    message: Message, session: AsyncSession, user: User
) -> None:
    payment = message.successful_payment
    plan_info = PLAN_PAYLOADS.get(payment.invoice_payload)
    if plan_info is None:
        logger.warning("Unknown successful payment payload: %s", payment.invoice_payload)
        return
    plan, _expected_amount = plan_info
    try:
        await crud.activate_subscription(
            session,
            telegram_id=user.telegram_id,
            plan_type=plan,
            stars_amount=payment.total_amount,
            telegram_payment_charge_id=payment.telegram_payment_charge_id,
            days=30,
        )
    except Exception:
        logger.exception("Failed to activate subscription for %s", user.telegram_id)
        await message.answer(
            "Платёж получен, но не удалось активировать подписку автоматически."
            " Напишите в поддержку — мы поможем."
        )
        return
    await message.answer(
        f"✨ Подписка активирована до конца месяца. Спасибо, что поддерживаете"
        f" Stellarium AI! Возврат возможен в течение 21 дня согласно правилам"
        f" Telegram Stars."
    )
