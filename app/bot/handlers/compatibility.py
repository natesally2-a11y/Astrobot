"""Compatibility (synastry) flow."""
from __future__ import annotations

import re
from datetime import date, datetime, time

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import compatibility as compat_text
from app.astrology.calculations import compute_chart, synastry_score
from app.astrology.geocoding import geocode
from app.bot import texts
from app.bot.states import CompatibilityFlow
from app.bot.utils.access import (
    ensure_birth_data,
    ensure_consent,
    require_premium,
    spend_free_question,
)
from app.database.crud import add_reading
from app.database.models import User

router = Router(name="compatibility")


@router.message(Command("compatibility"))
async def cmd_compatibility(
    message: Message, session: AsyncSession, user: User, state: FSMContext
) -> None:
    if not await ensure_consent(user, message):
        return
    if await ensure_birth_data(user, session, message) is None:
        return
    if not await spend_free_question(user, message):
        return

    await message.answer(texts.ASK_FOR_PARTNER_BIRTH, parse_mode="HTML")
    await state.set_state(CompatibilityFlow.waiting_partner)


PARTNER_RE = re.compile(
    r"^(?P<date>\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})"
    r"(?:\s+(?P<time>\d{1,2}:\d{2}))?"
    r"\s+(?P<place>.+)$"
)


@router.message(StateFilter(CompatibilityFlow.waiting_partner), F.text)
async def take_partner(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    m = PARTNER_RE.match(message.text.strip())
    if not m:
        await message.answer("Формат: <code>14.02.1990 09:30 Москва</code>", parse_mode="HTML")
        return

    date_str = m.group("date").replace("/", ".").replace("-", ".")
    parsed_date: date | None = None
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            break
        except ValueError:
            continue
    if parsed_date is None:
        await message.answer("Неверная дата. Пример: 14.02.1990")
        return

    parsed_time: time | None = None
    if m.group("time"):
        try:
            parsed_time = datetime.strptime(m.group("time"), "%H:%M").time()
        except ValueError:
            parsed_time = None

    place_q = m.group("place").strip()
    results = await geocode(place_q, limit=1)
    if not results:
        await message.answer("Не нашёл город. Уточните формулировку и попробуйте ещё раз.")
        return
    geo = results[0]

    bd = (await session.get(type(user), user.telegram_id)).birth_data
    if bd is None:
        bd = None  # already checked but mypy safety
    own = await _fetch_birth(session, user.telegram_id)
    if own is None:
        await message.answer("Сначала сохраните свои данные через /start.")
        await state.clear()
        return

    placeholder = await message.answer("💞 Считаю синастрию…")

    chart_a = compute_chart(
        birth_date=own.birth_date,
        birth_time=None if own.time_is_unknown else own.birth_time,
        latitude=float(own.latitude),
        longitude=float(own.longitude),
        timezone_name=own.timezone,
    )
    chart_b = compute_chart(
        birth_date=parsed_date,
        birth_time=parsed_time,
        latitude=geo.latitude,
        longitude=geo.longitude,
    )
    score, highlights = synastry_score(chart_a, chart_b)
    text = await compat_text(
        chart_a, chart_b,
        score=score, highlights=highlights,
        name_a=own.name, name_b="партнёр",
    )
    await add_reading(
        session,
        user_id=user.telegram_id,
        reading_type="compatibility",
        ai_response=text,
        question=f"{date_str} {m.group('time') or '?'} {place_q}",
    )
    await placeholder.delete()
    await message.answer(f"💞 Индекс совместимости: <b>{score}/100</b>", parse_mode="HTML")
    for chunk in _split(text, 3800):
        await message.answer(chunk)
    await state.clear()


async def _fetch_birth(session: AsyncSession, user_id: int):
    from app.database.crud import get_birth_data
    return await get_birth_data(session, user_id)


def _split(text: str, n: int):
    for i in range(0, len(text), n):
        yield text[i : i + n]
