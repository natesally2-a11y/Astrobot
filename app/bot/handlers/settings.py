"""/settings — subscription status, profile and referral management."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import settings_keyboard, subscription_keyboard
from app.bot.plans import PLANS, plan_features_text
from app.bot.utils import has_premium, referral_link
from app.config import settings as cfg
from app.database import crud
from app.database.models import PLAN_FREE, User

router = Router(name="settings")


def _status_text(user: User) -> str:
    if user.subscription_type == PLAN_FREE:
        plan_name = "Бесплатный"
        expiry = ""
    else:
        plan_name = PLANS[user.subscription_type].title if user.subscription_type in PLANS else user.subscription_type
        expiry = (
            f"\nДействует до: *{user.subscription_expires_at:%d.%m.%Y}*"
            if user.subscription_expires_at
            else ""
        )

    left = ""
    if user.subscription_type == PLAN_FREE:
        remaining = max(0, cfg.free_daily_questions - (user.questions_used_today or 0))
        left = f"\nБесплатных вопросов сегодня: *{remaining}/{cfg.free_daily_questions}*"

    return (
        "⚙️ *Настройки и подписка*\n\n"
        f"Текущий тариф: *{plan_name}*{expiry}{left}\n\n"
        f"Приглашено друзей: *{user.referral_count}* "
        "(каждый друг = +7 дней Premium 🎁)"
    )


@router.message(Command("settings"))
async def cmd_settings(message: Message, user: User) -> None:
    await message.answer(
        _status_text(user),
        parse_mode="Markdown",
        reply_markup=settings_keyboard(referral_link(user.telegram_id)),
    )


@router.callback_query(F.data == "menu:settings")
async def cb_settings(callback: CallbackQuery, user: User) -> None:
    await callback.message.answer(
        _status_text(user),
        parse_mode="Markdown",
        reply_markup=settings_keyboard(referral_link(user.telegram_id)),
    )
    await callback.answer()


@router.callback_query(F.data.in_({"menu:subscribe", "menu:upgrade"}))
async def cb_subscribe(callback: CallbackQuery) -> None:
    text = "⭐ *Подписки Stellarium AI*\n\n"
    text += "\n\n".join(plan_features_text(p) for p in PLANS.values())
    text += "\n\nОплата проходит через *Telegram Stars* ⭐ — быстро и безопасно."
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=subscription_keyboard())
    await callback.answer()
