"""Subscription menu, settings."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import (
    confirm_delete_kb,
    settings_kb,
    subscription_kb,
)
from app.bot.utils.access import format_expires, has_active_premium, plan_label
from app.config import settings
from app.database import crud
from app.database.models import User

router = Router(name="subscription")


@router.message(Command("settings"))
async def cmd_settings(message: Message, session: AsyncSession, user: User) -> None:
    await _show_settings(message, session, user)


@router.callback_query(F.data == "menu:settings")
async def cb_settings(
    callback: CallbackQuery, session: AsyncSession, user: User
) -> None:
    await _show_settings(callback.message, session, user)
    await callback.answer()


async def _show_settings(message: Message, session: AsyncSession, user: User) -> None:
    birth = await crud.get_birth_data(session, user.telegram_id)
    plan = plan_label(user)
    expires = format_expires(user) if has_active_premium(user) else "—"
    lines = [
        f"<b>Настройки</b>",
        f"Имя: {user.first_name or '—'}",
        f"Username: @{user.username}" if user.username else "Username: —",
        f"Подписка: <b>{plan}</b>",
        f"Действует до: {expires}",
    ]
    if birth:
        lines.append(
            f"Место рождения: {birth.birth_place} ({birth.birth_date.strftime('%d.%m.%Y')})"
        )
    else:
        lines.append("Натальная карта ещё не создана.")
    await message.answer("\n".join(lines), reply_markup=settings_kb(), parse_mode="HTML")


@router.callback_query(F.data == "menu:subscription")
async def cb_subscription(callback: CallbackQuery, user: User) -> None:
    await _show_subscription(callback.message, user)
    await callback.answer()


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message, user: User) -> None:
    await _show_subscription(message, user)


async def _show_subscription(message: Message, user: User) -> None:
    text = (
        "<b>💳 Тарифные планы Stellarium AI</b>\n\n"
        "<b>Free</b> — натальная карта, базовый анализ, 5 вопросов в день.\n\n"
        f"<b>Stellarium Pro — {settings.pro_price_stars} ⭐ / мес</b>\n"
        "• Подробные ежедневные и недельные прогнозы\n"
        "• Анализ совместимости\n"
        "• Безлимитные вопросы ИИ\n"
        "• Уведомления о транзитах\n\n"
        f"<b>Космический Оракул — {settings.oracle_price_stars} ⭐ / мес</b>\n"
        "• Всё из Pro\n"
        "• Бизнес-астрология и благоприятные даты\n"
        "• Годовые прогнозы\n"
        "• Индивидуальные ритуалы\n"
        "• Приоритетная поддержка ИИ\n\n"
        f"Текущий план: <b>{plan_label(user)}</b>"
    )
    await message.answer(text, reply_markup=subscription_kb(), parse_mode="HTML")


@router.callback_query(F.data == "data:delete")
async def cb_data_delete(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Точно удалить все данные? Это действие необратимо.",
        reply_markup=confirm_delete_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "data:delete:yes")
async def cb_data_delete_confirm(
    callback: CallbackQuery, session: AsyncSession, user: User
) -> None:
    await crud.delete_user(session, user.telegram_id)
    await callback.message.answer(
        "Все ваши данные удалены. Если захотите вернуться — нажмите /start."
    )
    await callback.answer("Удалено")
