"""/start, /help, main menu navigation."""

from __future__ import annotations

import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import (
    gdpr_kb,
    main_menu_kb,
    start_kb,
)
from app.bot.texts import (
    DISCLAIMER,
    GDPR_TEXT,
    HELP_TEXT,
    PRIVACY_TEXT,
    WELCOME,
    subscription_status_text,
)
from app.bot.utils.access import format_expires, has_active_premium, plan_label
from app.config import settings
from app.database import crud
from app.database.models import User

logger = logging.getLogger(__name__)
router = Router(name="common")


def _parse_referrer(command: CommandObject) -> Optional[int]:
    args = (command.args or "").strip()
    if args.startswith("ref_"):
        rest = args[4:]
        if rest.isdigit():
            return int(rest)
    return None


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    user: User,
) -> None:
    referrer = _parse_referrer(command)
    if referrer and referrer != user.telegram_id and user.referrer_id is None:
        user.referrer_id = referrer
        await session.commit()
        try:
            await crud.extend_premium_days(session, referrer, days=7)
        except Exception:
            logger.exception("Failed to credit referrer %s", referrer)

    await message.answer(WELCOME, reply_markup=start_kb(), parse_mode="HTML")
    await message.answer(DISCLAIMER, parse_mode="HTML")

    if not user.gdpr_consent:
        await message.answer(GDPR_TEXT, reply_markup=gdpr_kb(), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = HELP_TEXT + "\n" + DISCLAIMER
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "show:help")
async def show_help(callback: CallbackQuery) -> None:
    await callback.message.answer(HELP_TEXT, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "show:privacy")
async def show_privacy(callback: CallbackQuery) -> None:
    await callback.message.answer(PRIVACY_TEXT, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gdpr:accept")
async def gdpr_accept(
    callback: CallbackQuery, session: AsyncSession, user: User
) -> None:
    await crud.set_gdpr_consent(session, user.telegram_id)
    user.gdpr_consent = True
    await callback.message.answer(
        "Спасибо! Согласие сохранено. Нажмите кнопку ниже, чтобы создать"
        " вашу натальную карту 🌟",
        reply_markup=start_kb(),
    )
    await callback.answer("Готово")


@router.callback_query(F.data == "menu:back")
async def menu_back(
    callback: CallbackQuery, session: AsyncSession, user: User
) -> None:
    await _send_main_menu(callback.message, session, user)
    await callback.answer()


@router.message(Command("menu"))
async def cmd_menu(message: Message, session: AsyncSession, user: User) -> None:
    await _send_main_menu(message, session, user)


async def _send_main_menu(message: Message, session: AsyncSession, user: User) -> None:
    birth = await crud.get_birth_data(session, user.telegram_id)
    asked_today = await crud.count_questions_today(session, user.telegram_id)
    plan = plan_label(user)
    expires = format_expires(user) if has_active_premium(user) else None
    status = subscription_status_text(
        plan if has_active_premium(user) else "free",
        expires,
        asked_today,
        settings.free_daily_questions,
    )
    await message.answer(
        f"<b>Главное меню</b>\n\n{status}",
        reply_markup=main_menu_kb(birth is not None),
        parse_mode="HTML",
    )
