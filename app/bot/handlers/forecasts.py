"""Прогнозы: /today, /week, /transit."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import (
    interpret_daily,
    interpret_period,
    interpret_transits,
)
from app.bot import texts
from app.bot.handlers.common import require_chart, require_premium
from app.bot.utils import reply_long
from app.database import crud
from app.plans import is_premium

router = Router(name="forecasts")


async def _today(message: Message, session: AsyncSession, user_id: int) -> None:
    chart = await require_chart(message, session, user_id)
    if chart is None:
        return
    user = await crud.get_user(session, user_id)
    detailed = bool(user and is_premium(user.subscription_type) and crud.is_subscription_active(user))

    status = await message.answer(texts.THINKING)
    text = await interpret_daily(chart, detailed=detailed)
    await status.delete()
    title = "🌤 <b>Подробный прогноз на сегодня</b>" if detailed else "🌤 <b>Прогноз на сегодня</b>"
    await reply_long(message, f"{title}\n\n{text}")
    await crud.save_reading(session, user_id, "daily", text)


@router.message(Command("today"))
async def cmd_today(message: Message, session: AsyncSession) -> None:
    await _today(message, session, message.from_user.id)


@router.callback_query(F.data == "menu:today")
async def cb_today(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    await _today(call.message, session, call.from_user.id)


@router.message(Command("week"))
async def cmd_week(message: Message, session: AsyncSession) -> None:
    if not await require_premium(message, session, message.from_user.id):
        return
    chart = await require_chart(message, session, message.from_user.id)
    if chart is None:
        return
    status = await message.answer(texts.THINKING)
    text = await interpret_period(chart, "неделю")
    await status.delete()
    await reply_long(message, "📅 <b>Прогноз на неделю</b>\n\n" + text)
    await crud.save_reading(session, message.from_user.id, "weekly", text)


@router.message(Command("transit"))
async def cmd_transit(message: Message, session: AsyncSession) -> None:
    if not await require_premium(message, session, message.from_user.id):
        return
    chart = await require_chart(message, session, message.from_user.id)
    if chart is None:
        return
    status = await message.answer(texts.THINKING)
    text = await interpret_transits(chart)
    await status.delete()
    await reply_long(message, "🪐 <b>Важные транзиты</b>\n\n" + text)
    await crud.save_reading(session, message.from_user.id, "transit", text)
