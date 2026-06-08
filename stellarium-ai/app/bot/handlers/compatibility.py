"""
/compatibility command handler — Synastry analysis.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import crud
from app.database.models import User
from app.astrology.calculations import NatalChart
from app.astrology.ai_interpreter import get_compatibility
from app.bot.keyboards.inline import (
    get_year_keyboard, get_month_keyboard, get_day_keyboard,
    get_birth_time_keyboard, get_main_menu_keyboard,
    MonthCD, DayCD, YearCD, TimeCD,
)
from app.bot.states import CompatibilityStates

router = Router(name="compatibility")

MONTH_NAMES = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]


@router.message(Command("compatibility"))
async def cmd_compatibility(message: Message, state: FSMContext, session=None, db_user: Optional[User] = None):
    await start_compatibility(message, state, session, db_user)


async def start_compatibility(
    message: Message,
    state: FSMContext,
    session=None,
    db_user: Optional[User] = None,
):
    user_id = message.chat.id
    birth_data = await crud.get_birth_data(session, user_id) if session else None
    if not birth_data:
        await message.answer("❌ Данные рождения не найдены. Используйте /start.")
        return

    await state.clear()
    await state.set_state(CompatibilityStates.waiting_for_partner_name)
    await message.answer(
        "💕 <b>Анализ совместимости</b>\n\n"
        "Введите имя партнёра (или нажмите Enter для «Партнёр»):",
        parse_mode="HTML",
    )


@router.message(CompatibilityStates.waiting_for_partner_name)
async def process_partner_name(message: Message, state: FSMContext):
    name = message.text.strip() or "Партнёр"
    await state.update_data(partner_name=name)
    await message.answer(
        f"💕 Отлично! Введём данные для <b>{name}</b>\n\n"
        "📅 <b>Год рождения партнёра:</b>",
        parse_mode="HTML",
        reply_markup=get_year_keyboard(),
    )
    await state.set_state(CompatibilityStates.waiting_for_partner_year)


@router.callback_query(YearCD.filter(), CompatibilityStates.waiting_for_partner_year)
async def partner_year(callback: CallbackQuery, callback_data: YearCD, state: FSMContext):
    await state.update_data(partner_year=callback_data.year)
    await callback.answer(f"Год: {callback_data.year}")
    await callback.message.edit_text(
        f"📅 Год: <b>{callback_data.year}</b> ✓\n\n"
        "📅 <b>Месяц рождения партнёра:</b>",
        parse_mode="HTML",
        reply_markup=get_month_keyboard(),
    )
    await state.set_state(CompatibilityStates.waiting_for_partner_month)


@router.callback_query(MonthCD.filter(), CompatibilityStates.waiting_for_partner_month)
async def partner_month(callback: CallbackQuery, callback_data: MonthCD, state: FSMContext):
    await state.update_data(partner_month=callback_data.month)
    await callback.answer(f"Месяц: {MONTH_NAMES[callback_data.month - 1]}")
    await callback.message.edit_text(
        f"📅 Месяц: <b>{MONTH_NAMES[callback_data.month - 1]}</b> ✓\n\n"
        "📅 <b>День рождения партнёра:</b>",
        parse_mode="HTML",
        reply_markup=get_day_keyboard(callback_data.month),
    )
    await state.set_state(CompatibilityStates.waiting_for_partner_day)


@router.callback_query(DayCD.filter(), CompatibilityStates.waiting_for_partner_day)
async def partner_day(callback: CallbackQuery, callback_data: DayCD, state: FSMContext):
    data = await state.get_data()
    year = data.get("partner_year", 2000)
    try:
        birth_date = date(year, callback_data.month, callback_data.day)
        await state.update_data(partner_date=birth_date.isoformat())
    except ValueError:
        await callback.message.answer("❌ Некорректная дата.")
        return

    await callback.answer(f"День: {callback_data.day}")
    await callback.message.edit_text(
        f"📅 Дата: <b>{callback_data.day:02d}.{callback_data.month:02d}.{year}</b> ✓\n\n"
        "⏰ <b>Время рождения партнёра:</b>",
        parse_mode="HTML",
        reply_markup=get_birth_time_keyboard(),
    )
    await state.set_state(CompatibilityStates.waiting_for_partner_time)


@router.callback_query(TimeCD.filter(), CompatibilityStates.waiting_for_partner_time)
async def partner_time(callback: CallbackQuery, callback_data: TimeCD, state: FSMContext):
    await state.update_data(partner_time=callback_data.value)
    time_display = "Не указано" if callback_data.value == "unknown" else callback_data.value
    await callback.answer(f"Время: {time_display}")
    await callback.message.edit_text(
        f"⏰ Время: <b>{time_display}</b> ✓\n\n"
        "📍 <b>Место рождения партнёра:</b>\n\n"
        "Введите город:",
        parse_mode="HTML",
    )
    await state.set_state(CompatibilityStates.waiting_for_partner_place)


@router.message(CompatibilityStates.waiting_for_partner_place)
async def partner_place(message: Message, state: FSMContext, session=None, db_user: Optional[User] = None):
    from app.bot.handlers.start import _geocode_place

    place_name = message.text.strip()
    lat, lon, tz, full_place = await _geocode_place(place_name)

    if lat is None:
        lat, lon, tz = 55.75, 37.62, "Europe/Moscow"
        full_place = place_name

    data = await state.get_data()
    partner_date = date.fromisoformat(data["partner_date"])
    partner_time_str = data.get("partner_time", "unknown")
    partner_name = data.get("partner_name", "Партнёр")

    partner_time_obj = None
    if partner_time_str != "unknown":
        try:
            h, m = map(int, partner_time_str.split(":"))
            partner_time_obj = datetime(2000, 1, 1, h, m).time()
        except Exception:
            pass

    await state.clear()

    user = db_user or await crud.get_user(session, message.from_user.id)
    user_id = message.from_user.id
    user_name = user.display_name if user else "Вы"

    birth_data = await crud.get_birth_data(session, user_id)
    if not birth_data:
        await message.answer("❌ Данные рождения не найдены.")
        return

    msg = await message.answer("💕 Анализирую совместимость...")

    try:
        chart1 = NatalChart(
            birth_date=birth_data.birth_date,
            birth_time=birth_data.birth_time,
            latitude=float(birth_data.latitude or 55.75),
            longitude=float(birth_data.longitude or 37.62),
            timezone=birth_data.timezone or "Europe/Moscow",
        )

        chart2 = NatalChart(
            birth_date=partner_date,
            birth_time=partner_time_obj,
            latitude=lat,
            longitude=lon,
            timezone=tz,
        )

        analysis = await get_compatibility(chart1, user_name, chart2, partner_name)
        await crud.save_reading(session, user_id, "compatibility", partner_name, analysis)

        sun1 = chart1.get_sun_sign()
        sun2 = chart2.get_sun_sign()

        await msg.delete()
        await message.answer(
            f"💕 <b>Совместимость: {user_name} & {partner_name}</b>\n"
            f"☉ {sun1} × ☉ {sun2}\n\n"
            f"{analysis}",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(
                has_birth_data=True, is_pro=user.is_pro if user else False
            ),
        )
    except Exception:
        await msg.delete()
        await message.answer("❌ Ошибка при анализе совместимости. Попробуйте позже.")
