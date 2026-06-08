"""Step-by-step birth data collection with an FSM."""

from __future__ import annotations

import logging
from datetime import date, time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.geocoding import geocode_city
from app.bot.keyboards.inline import (
    calendar_kb,
    cancel_kb,
    confirm_geo_kb,
    hours_kb,
    main_menu_kb,
    minutes_kb,
)
from app.bot.texts import GDPR_TEXT
from app.bot.keyboards.inline import gdpr_kb
from app.database import crud
from app.database.models import User

logger = logging.getLogger(__name__)
router = Router(name="onboarding")


class Onboarding(StatesGroup):
    waiting_date = State()
    waiting_hour = State()
    waiting_minute = State()
    waiting_city = State()
    confirming_city = State()


@router.callback_query(F.data == "onboard:start")
async def onboard_start(
    callback: CallbackQuery, state: FSMContext, user: User
) -> None:
    if not user.gdpr_consent:
        await callback.message.answer(GDPR_TEXT, reply_markup=gdpr_kb(), parse_mode="HTML")
        await callback.answer()
        return
    today = date.today()
    await state.set_state(Onboarding.waiting_date)
    await callback.message.answer(
        "📅 Выберите дату рождения:",
        reply_markup=calendar_kb(today.year - 25, today.month),
    )
    await callback.answer()


@router.callback_query(F.data == "onboard:restart")
async def onboard_restart(
    callback: CallbackQuery, state: FSMContext, user: User
) -> None:
    if not user.gdpr_consent:
        await callback.message.answer(GDPR_TEXT, reply_markup=gdpr_kb(), parse_mode="HTML")
        await callback.answer()
        return
    today = date.today()
    await state.clear()
    await state.set_state(Onboarding.waiting_date)
    await callback.message.answer(
        "📅 Выберите новую дату рождения:",
        reply_markup=calendar_kb(today.year - 25, today.month),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cal:nav:"))
async def calendar_nav(callback: CallbackQuery) -> None:
    _, _, year, month, delta = callback.data.split(":")
    year, month, delta = int(year), int(month), int(delta)
    month += delta
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    await callback.message.edit_reply_markup(reply_markup=calendar_kb(year, month))
    await callback.answer()


@router.callback_query(F.data.startswith("cal:year:"))
async def calendar_year(callback: CallbackQuery) -> None:
    _, _, year, month = callback.data.split(":")
    await callback.message.edit_reply_markup(
        reply_markup=calendar_kb(int(year), int(month))
    )
    await callback.answer()


@router.callback_query(F.data == "cal:noop")
async def calendar_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("cal:pick:"))
async def calendar_pick(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, year, month, day = callback.data.split(":")
    birth_date = date(int(year), int(month), int(day))
    if birth_date > date.today():
        await callback.answer("Дата не может быть в будущем", show_alert=True)
        return
    await state.update_data(birth_date=birth_date.isoformat())
    await state.set_state(Onboarding.waiting_hour)
    await callback.message.answer(
        f"📅 Выбрано: <b>{birth_date.strftime('%d.%m.%Y')}</b>\n\n"
        "⏰ Теперь выберите час рождения. Чем точнее — тем точнее карта.",
        reply_markup=hours_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "time:unknown")
async def time_unknown(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(birth_time=None)
    await state.set_state(Onboarding.waiting_city)
    await callback.message.answer(
        "Хорошо, используем полдень как ориентир — Asc и дома могут быть"
        " приблизительными.\n\n📍 Введите город рождения:",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("time:h:"))
async def pick_hour(callback: CallbackQuery, state: FSMContext) -> None:
    hour = int(callback.data.split(":")[2])
    await state.update_data(hour=hour)
    await state.set_state(Onboarding.waiting_minute)
    await callback.message.answer(
        f"Час: <b>{hour:02d}</b>\nВыберите минуты:",
        reply_markup=minutes_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("time:m:"))
async def pick_minute(callback: CallbackQuery, state: FSMContext) -> None:
    minute = int(callback.data.split(":")[2])
    data = await state.get_data()
    hour = data.get("hour", 12)
    birth_time = time(hour, minute)
    await state.update_data(birth_time=birth_time.isoformat())
    await state.set_state(Onboarding.waiting_city)
    await callback.message.answer(
        f"⏰ Время: <b>{birth_time.strftime('%H:%M')}</b>\n\n"
        "📍 Введите город рождения (например, Москва):",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Onboarding.waiting_city)
async def city_input(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    query = (message.text or "").strip()
    if len(query) < 2:
        await message.answer("Введите название города (минимум 2 символа).")
        return
    await message.answer("🔎 Ищу координаты…")
    geo = await geocode_city(query)
    if geo is None:
        await message.answer(
            "Не удалось найти этот город. Попробуйте другое название или формат"
            " «Город, Страна»."
        )
        return
    await state.update_data(
        city_display=geo.display_name,
        latitude=geo.latitude,
        longitude=geo.longitude,
        timezone=geo.timezone,
    )
    await state.set_state(Onboarding.confirming_city)
    await message.answer(
        f"📍 Нашёл: <b>{geo.display_name}</b>\n"
        f"Координаты: {geo.latitude:.4f}, {geo.longitude:.4f}\n"
        f"Часовой пояс: {geo.timezone}\n\nЭто правильное место?",
        reply_markup=confirm_geo_kb(query),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "geo:retry")
async def geo_retry(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Onboarding.waiting_city)
    await callback.message.answer("Введите город рождения ещё раз:")
    await callback.answer()


@router.callback_query(F.data == "geo:ok")
async def geo_ok(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    data = await state.get_data()
    birth_date_iso = data.get("birth_date")
    birth_time_iso = data.get("birth_time")
    if not birth_date_iso:
        await callback.message.answer("Что-то пошло не так, начнём сначала /start")
        await state.clear()
        await callback.answer()
        return
    birth_date_obj = date.fromisoformat(birth_date_iso)
    birth_time_obj = time.fromisoformat(birth_time_iso) if birth_time_iso else None
    await crud.upsert_birth_data(
        session,
        user.telegram_id,
        birth_date=birth_date_obj,
        birth_time=birth_time_obj,
        birth_place=data.get("city_display", ""),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        tz_name=data.get("timezone"),
    )
    await state.clear()
    await callback.message.answer(
        "🌟 Натальная карта сохранена! Откройте её командой /chart или нажмите"
        " кнопку ниже.",
        reply_markup=main_menu_kb(has_chart=True),
    )
    await callback.answer("Готово")
