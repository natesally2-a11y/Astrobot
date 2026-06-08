"""Daily / weekly / transit forecasts."""
from __future__ import annotations

from datetime import date, time, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import daily_forecast, transit_brief, weekly_forecast
from app.astrology.calculations import compute_chart
from app.bot.utils.access import (
    ensure_birth_data,
    ensure_consent,
    require_premium,
    spend_free_question,
)
from app.database.crud import add_reading
from app.database.models import User

router = Router(name="forecasts")


def _natal_from(bd) -> "object":
    return compute_chart(
        birth_date=bd.birth_date,
        birth_time=None if bd.time_is_unknown else bd.birth_time,
        latitude=float(bd.latitude),
        longitude=float(bd.longitude),
        timezone_name=bd.timezone,
    )


def _transit_for(day: date):
    return compute_chart(
        birth_date=day,
        birth_time=time(12, 0),
        latitude=0.0,
        longitude=0.0,
        timezone_name="UTC",
    )


@router.message(Command("today"))
async def cmd_today(message: Message, session: AsyncSession, user: User) -> None:
    if not await ensure_consent(user, message):
        return
    bd = await ensure_birth_data(user, session, message)
    if bd is None:
        return
    if not await spend_free_question(user, message):
        return

    placeholder = await message.answer("🌙 Считаю транзиты на сегодня…")
    chart = _natal_from(bd)
    transits = _transit_for(date.today())
    text = await daily_forecast(chart, transits, name=bd.name)
    await add_reading(
        session, user_id=user.telegram_id, reading_type="daily", ai_response=text
    )
    await placeholder.delete()
    await message.answer(text)


@router.message(Command("week"))
async def cmd_week(message: Message, session: AsyncSession, user: User) -> None:
    if not await ensure_consent(user, message):
        return
    bd = await ensure_birth_data(user, session, message)
    if bd is None:
        return
    if not await require_premium(user, message, plan="pro"):
        return

    placeholder = await message.answer("🌌 Составляю прогноз на неделю…")
    chart = _natal_from(bd)
    transits = _transit_for(date.today() + timedelta(days=3))
    text = await weekly_forecast(chart, transits, name=bd.name)
    await add_reading(
        session, user_id=user.telegram_id, reading_type="weekly", ai_response=text
    )
    await placeholder.delete()
    for chunk in _split(text, 3800):
        await message.answer(chunk)


@router.message(Command("transit"))
async def cmd_transit(message: Message, session: AsyncSession, user: User) -> None:
    if not await ensure_consent(user, message):
        return
    bd = await ensure_birth_data(user, session, message)
    if bd is None:
        return
    if not await require_premium(user, message, plan="pro"):
        return

    placeholder = await message.answer("🪐 Анализирую важные транзиты…")
    chart = _natal_from(bd)
    transits = _transit_for(date.today())
    text = await transit_brief(chart, transits)
    await add_reading(
        session, user_id=user.telegram_id, reading_type="transit", ai_response=text
    )
    await placeholder.delete()
    await message.answer(text)


def _split(text: str, n: int):
    for i in range(0, len(text), n):
        yield text[i : i + n]
