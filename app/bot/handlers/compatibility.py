"""/compatibility — synastry between the user and a partner."""
from __future__ import annotations

import datetime as dt
import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology import ai_interpreter
from app.astrology.geocoding import geocode_city
from app.astrology.service import build_chart
from app.bot import texts
from app.bot.handlers._common import chart_from_birth_data, get_birth_data_or_prompt
from app.bot.states import CompatibilityFlow
from app.database import crud
from app.database.models import User

router = Router(name="compatibility")

_DATE_RE = re.compile(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\s*$")
_TIME_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*$")


@router.message(Command("compatibility"))
async def cmd_compatibility(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    bd = await get_birth_data_or_prompt(message, session, user)
    if bd is None:
        return
    await state.set_state(CompatibilityFlow.partner_date)
    await message.answer(texts.ASK_COMPAT_PARTNER, parse_mode="Markdown")


@router.message(CompatibilityFlow.partner_date, F.text)
async def partner_date(message: Message, state: FSMContext) -> None:
    m = _DATE_RE.match(message.text)
    if not m:
        await message.answer(texts.DATA_INVALID_DATE)
        return
    try:
        d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        await message.answer(texts.DATA_INVALID_DATE)
        return
    await state.update_data(p_date=d.isoformat())
    await state.set_state(CompatibilityFlow.partner_time)
    await message.answer(texts.ASK_COMPAT_TIME, parse_mode="Markdown")


@router.message(CompatibilityFlow.partner_time, F.text)
async def partner_time(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text in {"-", "—"}:
        await state.update_data(p_time=None)
    else:
        m = _TIME_RE.match(text)
        if not m:
            await message.answer(texts.DATA_INVALID_TIME)
            return
        await state.update_data(p_time=f"{int(m.group(1)):02d}:{m.group(2)}")
    await state.set_state(CompatibilityFlow.partner_place)
    await message.answer(texts.ASK_COMPAT_PLACE)


@router.message(CompatibilityFlow.partner_place, F.text)
async def partner_place(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    data = await state.get_data()
    await state.clear()

    searching = await message.answer("🔍 Ищу город…")
    results = await geocode_city(message.text.strip())
    await searching.delete()
    if not results:
        await message.answer(texts.PLACE_NOT_FOUND + "\nПопробуйте снова: /compatibility")
        return
    place = results[0]

    p_date = dt.date.fromisoformat(data["p_date"])
    p_time = None
    if data.get("p_time"):
        h, mi = data["p_time"].split(":")
        p_time = dt.time(int(h), int(mi))

    thinking = await message.answer(texts.CALCULATING)
    bd = await crud.get_birth_data(session, user.telegram_id)
    chart_user = chart_from_birth_data(bd)
    chart_partner = build_chart(p_date, p_time, place.latitude, place.longitude, place.timezone)

    text = await ai_interpreter.interpret_compatibility(
        chart_user, chart_partner, name_a=user.first_name, name_b="Партнёр"
    )
    await crud.save_reading(session, user.telegram_id, "compatibility", text)
    await thinking.delete()
    await message.answer(f"💞 *Совместимость*\n\n{text}", parse_mode="Markdown")
