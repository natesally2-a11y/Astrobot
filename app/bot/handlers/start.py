"""Старт, GDPR-согласие и пошаговый сбор данных рождения."""
from __future__ import annotations

import datetime as dt
import logging

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.constants import sign_name
from app.bot import texts
from app.bot.keyboards.calendar import (
    build_calendar,
    build_cities,
    build_hours,
    build_minutes,
    default_calendar,
)
from app.bot.keyboards.common import (
    consent_keyboard,
    main_menu_keyboard,
    open_app_keyboard,
    start_keyboard,
)
from app.bot.states import Onboarding
from app.bot.utils import parse_referral, reply_long
from app.database import crud
from app.services.chart_service import chart_from_birth_data
from app.services.geocoding import geocode_city

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await state.clear()
    referred_by = parse_referral(command.args)
    user, created = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        language_code=message.from_user.language_code or "ru",
        referred_by=referred_by,
    )

    if created and user.referred_by:
        try:
            await crud.grant_referral_bonus(session, user.referred_by)
        except Exception as exc:  # pragma: no cover
            logger.warning("referral bonus failed: %s", exc)

    bd = await crud.get_birth_data(session, user.telegram_id)
    if bd is not None and user.gdpr_consent:
        await message.answer(
            f"С возвращением, {user.first_name or 'друг'}! ✨\n"
            "Чем займёмся сегодня?",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(texts.WELCOME, reply_markup=start_keyboard())


@router.callback_query(F.data == "onboard:start")
async def onboard_start(
    call: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    user = await crud.get_user(session, call.from_user.id)
    if user and user.gdpr_consent:
        await _begin_date(call.message, state)
    else:
        await call.message.answer(texts.GDPR_CONSENT, reply_markup=consent_keyboard())
    await call.answer()


@router.callback_query(F.data == "gdpr:accept")
async def gdpr_accept(
    call: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await crud.set_gdpr_consent(session, call.from_user.id)
    await call.answer("Согласие принято ✅")
    await _begin_date(call.message, state)


async def _begin_date(message: Message, state: FSMContext) -> None:
    await state.set_state(Onboarding.date)
    await message.answer(texts.ASK_DATE, reply_markup=default_calendar())


@router.callback_query(F.data.startswith("cal:"))
async def calendar_callback(call: CallbackQuery, state: FSMContext) -> None:
    parts = call.data.split(":")
    action = parts[1]

    if action == "ignore":
        await call.answer()
        return

    if action == "nav":
        year, month = int(parts[2]), int(parts[3])
        await call.message.edit_reply_markup(reply_markup=build_calendar(year, month))
        await call.answer()
        return

    if action == "day":
        year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
        try:
            chosen = dt.date(year, month, day)
        except ValueError:
            await call.answer("Некорректная дата", show_alert=True)
            return
        if chosen > dt.date.today():
            await call.answer("Дата рождения не может быть в будущем", show_alert=True)
            return

        await state.update_data(birth_date=chosen.isoformat())
        await state.set_state(Onboarding.time)
        await call.message.edit_text(
            f"📅 Дата: <b>{chosen.strftime('%d.%m.%Y')}</b>\n\n" + texts.ASK_TIME,
            reply_markup=build_hours(),
        )
        await call.answer()


@router.callback_query(Onboarding.time, F.data.startswith("time:"))
async def time_callback(call: CallbackQuery, state: FSMContext) -> None:
    parts = call.data.split(":")
    kind = parts[1]

    if kind == "unknown":
        await state.update_data(birth_time=None, time_is_exact=False)
        await state.set_state(Onboarding.place)
        await call.message.edit_text(
            "⏰ Время: <b>неизвестно</b> (используем полдень)\n\n" + texts.ASK_PLACE
        )
        await call.answer()
        return

    if kind == "h":
        hour = int(parts[2])
        await call.message.edit_reply_markup(reply_markup=build_minutes(hour))
        await call.answer()
        return

    if kind == "back":
        await call.message.edit_reply_markup(reply_markup=build_hours())
        await call.answer()
        return

    if kind == "m":
        hour, minute = int(parts[2]), int(parts[3])
        await state.update_data(
            birth_time=dt.time(hour, minute).isoformat(timespec="minutes"),
            time_is_exact=True,
        )
        await state.set_state(Onboarding.place)
        await call.message.edit_text(
            f"⏰ Время: <b>{hour:02d}:{minute:02d}</b>\n\n" + texts.ASK_PLACE
        )
        await call.answer()


@router.message(Onboarding.place, F.text)
async def place_input(message: Message, state: FSMContext) -> None:
    query = message.text.strip()
    status = await message.answer("🔎 Ищу город...")
    try:
        results = await geocode_city(query)
    except Exception as exc:  # pragma: no cover - сеть
        logger.error("geocode error: %s", exc)
        results = []

    if not results:
        await status.edit_text(texts.PLACE_NOT_FOUND)
        return

    await state.update_data(
        city_candidates=[
            {
                "name": r.display_name,
                "lat": r.latitude,
                "lon": r.longitude,
                "tz": r.timezone,
            }
            for r in results
        ]
    )
    await status.edit_text(
        "Выберите подходящий город:", reply_markup=build_cities(results)
    )


@router.callback_query(Onboarding.place, F.data.startswith("city:"))
async def city_chosen(
    call: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    idx = int(call.data.split(":")[1])
    data = await state.get_data()
    candidates = data.get("city_candidates", [])
    if idx >= len(candidates):
        await call.answer("Попробуйте ещё раз", show_alert=True)
        return
    city = candidates[idx]

    birth_date = dt.date.fromisoformat(data["birth_date"])
    birth_time = (
        dt.time.fromisoformat(data["birth_time"]) if data.get("birth_time") else None
    )
    time_is_exact = bool(data.get("time_is_exact", False))

    await call.message.edit_text(texts.CHART_BUILDING)

    bd = await crud.upsert_birth_data(
        session,
        telegram_id=call.from_user.id,
        birth_date=birth_date,
        birth_time=birth_time,
        time_is_exact=time_is_exact,
        birth_place=city["name"],
        latitude=city["lat"],
        longitude=city["lon"],
        timezone=city["tz"],
    )
    await state.clear()

    chart = chart_from_birth_data(bd)
    sun = chart.planet("sun")
    moon = chart.planet("moon")
    summary_lines = ["🌟 <b>Ваша натальная карта готова!</b>\n"]
    if sun:
        summary_lines.append(f"☉ Солнце: <b>{sun.sign}</b>")
    if moon:
        summary_lines.append(f"☽ Луна: <b>{moon.sign}</b>")
    if chart.ascendant is not None:
        summary_lines.append(f"↑ Асцендент: <b>{sign_name(chart.ascendant)}</b>")
    summary_lines.append("\nИспользуйте меню, чтобы получить чтения и прогнозы.")

    await reply_long(call.message, "\n".join(summary_lines))
    await call.message.answer(
        "Готово! Открывайте меню ниже 👇", reply_markup=main_menu_keyboard()
    )
    await call.message.answer(texts.DISCLAIMER)
    await call.answer()
