"""/today, /week (Premium), /transit (Premium) forecasts."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology import ai_interpreter
from app.astrology.calculations import calculate_transits
from app.bot import texts
from app.bot.handlers._common import chart_from_birth_data, get_birth_data_or_prompt
from app.bot.keyboards.inline import subscription_keyboard
from app.bot.utils import has_premium
from app.database import crud
from app.database.models import User

router = Router(name="forecast")


@router.message(Command("today"))
async def cmd_today(message: Message, session: AsyncSession, user: User) -> None:
    bd = await get_birth_data_or_prompt(message, session, user)
    if bd is None:
        return
    thinking = await message.answer(texts.CALCULATING)
    chart = chart_from_birth_data(bd)
    transits = calculate_transits(chart)
    text = await ai_interpreter.interpret_daily(chart, transits, name=user.first_name)
    await crud.save_reading(session, user.telegram_id, "daily", text)
    await thinking.delete()
    await message.answer(f"☀️ *Прогноз на сегодня*\n\n{text}", parse_mode="Markdown")


@router.message(Command("week"))
async def cmd_week(message: Message, session: AsyncSession, user: User) -> None:
    if not has_premium(user):
        await message.answer(
            texts.PREMIUM_ONLY.format(plan="Stellarium Pro"),
            parse_mode="Markdown",
            reply_markup=subscription_keyboard(),
        )
        return
    bd = await get_birth_data_or_prompt(message, session, user)
    if bd is None:
        return
    thinking = await message.answer(texts.CALCULATING)
    chart = chart_from_birth_data(bd)
    transits = calculate_transits(chart)
    text = await ai_interpreter.interpret_weekly(chart, transits, name=user.first_name)
    await crud.save_reading(session, user.telegram_id, "weekly", text)
    await thinking.delete()
    await message.answer(f"🗓 *Прогноз на неделю*\n\n{text}", parse_mode="Markdown")


@router.message(Command("transit"))
async def cmd_transit(message: Message, session: AsyncSession, user: User) -> None:
    if not has_premium(user):
        await message.answer(
            texts.PREMIUM_ONLY.format(plan="Stellarium Pro"),
            parse_mode="Markdown",
            reply_markup=subscription_keyboard(),
        )
        return
    bd = await get_birth_data_or_prompt(message, session, user)
    if bd is None:
        return
    thinking = await message.answer(texts.CALCULATING)
    chart = chart_from_birth_data(bd)
    transits = calculate_transits(chart)
    text = await ai_interpreter.interpret_transits(chart, transits, name=user.first_name)
    await crud.save_reading(session, user.telegram_id, "transit", text)
    await thinking.delete()
    await message.answer(f"🌠 *Важные транзиты*\n\n{text}", parse_mode="Markdown")
