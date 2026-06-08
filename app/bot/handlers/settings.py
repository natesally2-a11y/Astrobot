"""Команда /settings — профиль, подписка, реферальная программа."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import subscription_keyboard
from app.config import settings
from app.database import crud
from app.plans import get_plan

router = Router(name="settings")


async def _settings_text(session: AsyncSession, user_id: int) -> str:
    user = await crud.get_user(session, user_id)
    if not user:
        return "Профиль не найден. Нажмите /start."
    plan = get_plan(user.subscription_type)
    active = crud.is_subscription_active(user)

    status_line = "Бесплатный"
    if plan.is_paid and active and user.subscription_expires_at:
        exp = user.subscription_expires_at.strftime("%d.%m.%Y")
        status_line = f"{plan.title} (активна до {exp})"
    elif plan.is_paid and not active:
        status_line = f"{plan.title} (истекла)"

    bd = await crud.get_birth_data(session, user_id)
    birth_line = "не указаны"
    if bd:
        time_str = bd.birth_time.strftime("%H:%M") if bd.birth_time else "—"
        birth_line = (
            f"{bd.birth_date.strftime('%d.%m.%Y')} {time_str}, {bd.birth_place}"
        )

    lines = [
        "⚙️ <b>Настройки и подписка</b>\n",
        f"👤 Имя: {user.first_name or '—'}",
        f"🎂 Данные рождения: {birth_line}",
        f"💎 Тариф: <b>{status_line}</b>",
        f"🎁 Приглашено друзей: {user.referral_count}",
        "\n<b>Доступные тарифы:</b>",
    ]
    pro = get_plan("pro")
    oracle = get_plan("oracle")
    lines.append(f"\n⭐ <b>{pro.title}</b> — {pro.price_rub}₽/мес (~{pro.stars}★)")
    for f in pro.features:
        lines.append(f"  • {f}")
    lines.append(f"\n🌌 <b>{oracle.title}</b> — {oracle.price_rub}₽/мес (~{oracle.stars}★)")
    for f in oracle.features:
        lines.append(f"  • {f}")
    return "\n".join(lines)


@router.message(Command("settings"))
async def cmd_settings(message: Message, session: AsyncSession) -> None:
    user = await crud.get_user(session, message.from_user.id)
    text = await _settings_text(session, message.from_user.id)
    plan_code = user.subscription_type if user else "free"
    await message.answer(text, reply_markup=subscription_keyboard(plan_code))


@router.callback_query(F.data == "menu:settings")
async def cb_settings(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    user = await crud.get_user(session, call.from_user.id)
    text = await _settings_text(session, call.from_user.id)
    plan_code = user.subscription_type if user else "free"
    await call.message.answer(text, reply_markup=subscription_keyboard(plan_code))


@router.callback_query(F.data == "menu:referral")
async def cb_referral(call: CallbackQuery) -> None:
    await call.answer()
    link = f"https://t.me/{settings.bot_username}?start=ref_{call.from_user.id}"
    await call.message.answer(
        "🎁 <b>Реферальная программа</b>\n\n"
        "Приглашайте друзей и получайте <b>+1 неделю Premium</b> за каждого, "
        "кто запустит бота по вашей ссылке!\n\n"
        f"Ваша ссылка:\n{link}",
    )
