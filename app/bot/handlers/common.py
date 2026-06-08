"""Common handlers: /start, /help, /privacy."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.keyboards import consent_kb, main_menu_kb
from app.bot.states import Onboarding
from app.database.crud import get_birth_data
from app.database.models import User

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    # Referral payload — record once for new accounts.
    if command.args and command.args.startswith("ref_") and user.referred_by is None:
        try:
            referrer_id = int(command.args[4:])
            if referrer_id != user.telegram_id:
                user.referred_by = referrer_id
                # Reward the referrer with +7 days of Pro.
                from app.database.crud import add_referral_bonus_days
                await add_referral_bonus_days(session, referrer_id, 7)
        except ValueError:
            pass

    await state.clear()

    if not user.gdpr_consent:
        await message.answer(texts.WELCOME)
        await message.answer(texts.GDPR_CONSENT, reply_markup=consent_kb())
        await state.set_state(Onboarding.waiting_consent)
        return

    bd = await get_birth_data(session, user.telegram_id)
    if bd is None:
        await message.answer(
            "С возвращением! Давайте создадим вашу натальную карту. "
            "Как вас называть?"
        )
        await state.set_state(Onboarding.waiting_name)
        return

    await message.answer(
        f"С возвращением, {bd.name or user.first_name or 'друг'}! ✨\n\n"
        "Чем сегодня помочь?",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP_TEXT, parse_mode="HTML")


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=main_menu_kb())


@router.message(F.text == "/cancel")
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Окей, отменил. /menu — главное меню.")
