"""Команда /compatibility — синастрия двух натальных карт."""
from __future__ import annotations

import datetime as dt
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import interpret_compatibility
from app.bot import texts
from app.bot.handlers.common import require_chart
from app.bot.keyboards.calendar import (
    build_calendar,
    build_cities,
    build_hours,
    build_minutes,
    default_calendar,
)
from app.bot.states import CompatibilityFlow
from app.bot.utils import reply_long
from app.database import crud
from app.services.chart_service import chart_from_birth_data, chart_from_raw
from app.services.geocoding import geocode_city

logger = logging.getLogger(__name__)
router = Router(name="compatibility")

PRE_CAL = "ccal"
PRE_TIME = "ctime"
PRE_CITY = "ccity"


@router.message(Command("compatibility"))
async def cmd_compatibility(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    chart = await require_chart(message, session, message.from_user.id)
    if chart is None:
        return
    await state.set_state(CompatibilityFlow.name)
    await message.answer(
        "💞 <b>Анализ совместимости</b>\n\nКак зовут вашего партнёра?"
    )


@router.callback_query(F.data == "menu:compatibility")
async def cb_compatibility(
    call: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await call.answer()
    chart = await require_chart(call.message, session, call.from_user.id)
    if chart is None:
        return
    await state.set_state(CompatibilityFlow.name)
    await call.message.answer(
        "💞 <b>Анализ совместимости</b>\n\nКак зовут вашего партнёра?"
    )


@router.message(CompatibilityFlow.name, F.text)
async def comp_name(message: Message, state: FSMContext) -> None:
    await state.update_data(partner_name=message.text.strip()[:100])
    await state.set_state(CompatibilityFlow.date)
    await message.answer(
        "📅 Дата рождения партнёра:", reply_markup=default_calendar(PRE_CAL)
    )


@router.callback_query(CompatibilityFlow.date, F.data.startswith(f"{PRE_CAL}:"))
async def comp_date(call: CallbackQuery, state: FSMContext) -> None:
    parts = call.data.split(":")
    action = parts[1]
    if action == "ignore":
        await call.answer()
        return
    if action == "nav":
        year, month = int(parts[2]), int(parts[3])
        await call.message.edit_reply_markup(
            reply_markup=build_calendar(year, month, PRE_CAL)
        )
        await call.answer()
        return
    if action == "day":
        year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
        try:
            chosen = dt.date(year, month, day)
        except ValueError:
            await call.answer("Некорректная дата", show_alert=True)
            return
        await state.update_data(partner_date=chosen.isoformat())
        await state.set_state(CompatibilityFlow.time)
        await call.message.edit_text(
            f"📅 Дата партнёра: <b>{chosen.strftime('%d.%m.%Y')}</b>\n\n"
            "⏰ Время рождения партнёра:",
            reply_markup=build_hours(PRE_TIME),
        )
        await call.answer()


@router.callback_query(CompatibilityFlow.time, F.data.startswith(f"{PRE_TIME}:"))
async def comp_time(call: CallbackQuery, state: FSMContext) -> None:
    parts = call.data.split(":")
    kind = parts[1]
    if kind == "unknown":
        await state.update_data(partner_time=None)
        await state.set_state(CompatibilityFlow.place)
        await call.message.edit_text(
            "⏰ Время партнёра: <b>неизвестно</b>\n\n📍 Город рождения партнёра:"
        )
        await call.answer()
        return
    if kind == "h":
        await call.message.edit_reply_markup(
            reply_markup=build_minutes(int(parts[2]), PRE_TIME)
        )
        await call.answer()
        return
    if kind == "back":
        await call.message.edit_reply_markup(reply_markup=build_hours(PRE_TIME))
        await call.answer()
        return
    if kind == "m":
        hour, minute = int(parts[2]), int(parts[3])
        await state.update_data(
            partner_time=dt.time(hour, minute).isoformat(timespec="minutes")
        )
        await state.set_state(CompatibilityFlow.place)
        await call.message.edit_text(
            f"⏰ Время партнёра: <b>{hour:02d}:{minute:02d}</b>\n\n"
            "📍 Город рождения партнёра:"
        )
        await call.answer()


@router.message(CompatibilityFlow.place, F.text)
async def comp_place(message: Message, state: FSMContext) -> None:
    status = await message.answer("🔎 Ищу город...")
    try:
        results = await geocode_city(message.text.strip())
    except Exception as exc:  # pragma: no cover
        logger.error("geocode error: %s", exc)
        results = []
    if not results:
        await status.edit_text(texts.PLACE_NOT_FOUND)
        return
    await state.update_data(
        partner_cities=[
            {"name": r.display_name, "lat": r.latitude, "lon": r.longitude, "tz": r.timezone}
            for r in results
        ]
    )
    await status.edit_text(
        "Выберите город партнёра:", reply_markup=build_cities(results, PRE_CITY)
    )


@router.callback_query(CompatibilityFlow.place, F.data.startswith(f"{PRE_CITY}:"))
async def comp_city(
    call: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    idx = int(call.data.split(":")[1])
    data = await state.get_data()
    cities = data.get("partner_cities", [])
    if idx >= len(cities):
        await call.answer("Попробуйте снова", show_alert=True)
        return
    city = cities[idx]
    await state.clear()

    partner_date = dt.date.fromisoformat(data["partner_date"])
    partner_time = (
        dt.time.fromisoformat(data["partner_time"]) if data.get("partner_time") else None
    )
    partner_name = data.get("partner_name", "Партнёр")

    bd = await crud.get_birth_data(session, call.from_user.id)
    if bd is None:
        await call.message.edit_text(texts.NEED_BIRTH_DATA)
        await call.answer()
        return

    await call.message.edit_text("💞 Сравниваю карты...")

    user_chart = chart_from_birth_data(bd)
    partner_chart = chart_from_raw(
        partner_date, partner_time, city["lat"], city["lon"], city["tz"]
    )
    user = await crud.get_user(session, call.from_user.id)
    user_name = (user.first_name if user else None) or "Вы"

    text = await interpret_compatibility(
        user_chart, partner_chart, user_name, partner_name
    )
    await reply_long(
        call.message, f"💞 <b>Совместимость: {user_name} и {partner_name}</b>\n\n{text}"
    )
    await crud.save_reading(session, call.from_user.id, "compatibility", text)
    await call.answer()
