"""/start command, onboarding FSM and GDPR consent."""
from __future__ import annotations

import datetime as dt
import re

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.geocoding import geocode_city
from app.bot import texts
from app.bot.keyboards.calendar import CalendarCB, build_calendar
from app.bot.keyboards.inline import (
    consent_keyboard,
    main_menu_keyboard,
    place_choice_keyboard,
    start_keyboard,
    time_keyboard,
    webapp_keyboard,
)
from app.bot.states import Onboarding
from app.database import crud
from app.database.models import User

router = Router(name="start")

_DATE_RE = re.compile(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\s*$")
_TIME_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*$")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    await state.clear()

    # Referral handling: /start ref_<id>
    if command.args and command.args.startswith("ref_") and user.referred_by is None:
        try:
            referrer_id = int(command.args[4:])
        except ValueError:
            referrer_id = None
        if referrer_id and referrer_id != user.telegram_id:
            user.referred_by = referrer_id
            await crud.increment_referral(session, referrer_id)
            await crud.extend_premium(session, referrer_id, days=7)

    bd = await crud.get_birth_data(session, user.telegram_id)
    if bd is not None:
        await message.answer(
            f"С возвращением, {user.first_name or 'друг'}! ✨\nЧем займёмся сегодня?",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(texts.WELCOME, reply_markup=start_keyboard())


@router.callback_query(F.data == "onboard:start")
async def onboard_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Onboarding.date)
    await callback.message.answer(texts.ASK_BIRTH_DATE, reply_markup=build_calendar())
    await callback.answer()


# --------------------------------------------------------------------------
# Step 1: date — calendar navigation + text input
# --------------------------------------------------------------------------


@router.callback_query(Onboarding.date, CalendarCB.filter())
async def on_calendar(
    callback: CallbackQuery, callback_data: CalendarCB, state: FSMContext
) -> None:
    action = callback_data.action
    year, month = callback_data.year, callback_data.month

    if action == "ignore":
        await callback.answer()
        return
    if action == "prev-year":
        year -= 1
    elif action == "next-year":
        year += 1
    elif action == "prev-month":
        month -= 1
        if month < 1:
            month, year = 12, year - 1
    elif action == "next-month":
        month += 1
        if month > 12:
            month, year = 1, year + 1
    elif action == "day":
        chosen = dt.date(callback_data.year, callback_data.month, callback_data.day)
        if chosen > dt.date.today():
            await callback.answer("Дата рождения не может быть в будущем 🙂", show_alert=True)
            return
        await state.update_data(birth_date=chosen.isoformat())
        await state.set_state(Onboarding.time)
        await callback.message.edit_text(
            f"📅 Дата рождения: *{chosen.strftime('%d.%m.%Y')}*",
            parse_mode="Markdown",
        )
        await callback.message.answer(texts.ASK_BIRTH_TIME, reply_markup=time_keyboard())
        await callback.answer()
        return

    await callback.message.edit_reply_markup(reply_markup=build_calendar(year, month))
    await callback.answer()


@router.message(Onboarding.date, F.text)
async def on_date_text(message: Message, state: FSMContext) -> None:
    m = _DATE_RE.match(message.text)
    if not m:
        await message.answer(texts.DATA_INVALID_DATE)
        return
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        chosen = dt.date(year, month, day)
    except ValueError:
        await message.answer(texts.DATA_INVALID_DATE)
        return
    if chosen > dt.date.today():
        await message.answer("Дата рождения не может быть в будущем 🙂")
        return
    await state.update_data(birth_date=chosen.isoformat())
    await state.set_state(Onboarding.time)
    await message.answer(texts.ASK_BIRTH_TIME, reply_markup=time_keyboard())


# --------------------------------------------------------------------------
# Step 2: time
# --------------------------------------------------------------------------


@router.callback_query(Onboarding.time, F.data.startswith("time:"))
async def on_time_cb(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 1)[1]
    if value == "unknown":
        await state.update_data(birth_time=None, time_known=False)
    else:
        await state.update_data(birth_time=value, time_known=True)
    await state.set_state(Onboarding.place)
    await callback.message.answer(texts.ASK_BIRTH_PLACE)
    await callback.answer()


@router.message(Onboarding.time, F.text)
async def on_time_text(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text in {"-", "—", "не знаю", "Не знаю"}:
        await state.update_data(birth_time=None, time_known=False)
    else:
        m = _TIME_RE.match(text)
        if not m or not (0 <= int(m.group(1)) < 24 and 0 <= int(m.group(2)) < 60):
            await message.answer(texts.DATA_INVALID_TIME)
            return
        await state.update_data(birth_time=f"{int(m.group(1)):02d}:{m.group(2)}", time_known=True)
    await state.set_state(Onboarding.place)
    await message.answer(texts.ASK_BIRTH_PLACE)


# --------------------------------------------------------------------------
# Step 3: place — geocoding
# --------------------------------------------------------------------------


@router.message(Onboarding.place, F.text)
async def on_place_text(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    query = message.text.strip()
    searching = await message.answer("🔍 Ищу город…")
    results = await geocode_city(query)
    await searching.delete()

    if not results:
        await message.answer(texts.PLACE_NOT_FOUND)
        return

    if len(results) == 1:
        await _store_place(state, results[0])
        await _finish_or_consent(message, state, session, user)
        return

    # Stash candidates for the choice callback.
    await state.update_data(
        place_candidates=[
            {"name": r.name, "lat": r.latitude, "lon": r.longitude, "tz": r.timezone}
            for r in results
        ]
    )
    await state.set_state(Onboarding.place_choice)
    await message.answer(texts.CHOOSE_PLACE, reply_markup=place_choice_keyboard(results))


@router.callback_query(Onboarding.place_choice, F.data.startswith("place:"))
async def on_place_choice(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    candidates = data.get("place_candidates", [])
    if idx >= len(candidates):
        await callback.answer("Вариант не найден", show_alert=True)
        return
    chosen = candidates[idx]
    await state.update_data(
        birth_place=chosen["name"],
        latitude=chosen["lat"],
        longitude=chosen["lon"],
        timezone=chosen["tz"],
    )
    await callback.message.edit_text(f"📍 Место рождения: *{chosen['name']}*", parse_mode="Markdown")
    await _finish_or_consent(callback.message, state, session, user)
    await callback.answer()


async def _store_place(state: FSMContext, result) -> None:
    await state.update_data(
        birth_place=result.name,
        latitude=result.latitude,
        longitude=result.longitude,
        timezone=result.timezone,
    )


# --------------------------------------------------------------------------
# Consent + save
# --------------------------------------------------------------------------


async def _finish_or_consent(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    if user.gdpr_consent:
        await _save_profile(message, state, session, user)
    else:
        await state.set_state(Onboarding.consent)
        await message.answer(texts.GDPR_CONSENT, reply_markup=consent_keyboard())


@router.callback_query(Onboarding.consent, F.data == "gdpr:accept")
async def on_consent_accept(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    await crud.set_gdpr_consent(session, user.telegram_id, True)
    user.gdpr_consent = True
    await callback.message.edit_text("✅ Спасибо! Согласие получено.")
    await _save_profile(callback.message, state, session, user)
    await callback.answer()


async def _save_profile(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    data = await state.get_data()
    await state.clear()

    birth_date = dt.date.fromisoformat(data["birth_date"])
    birth_time = None
    time_known = data.get("time_known", False)
    if data.get("birth_time"):
        h, m = data["birth_time"].split(":")
        birth_time = dt.time(int(h), int(m))

    await crud.upsert_birth_data(
        session,
        user_id=user.telegram_id,
        birth_date=birth_date,
        birth_time=birth_time,
        time_known=time_known,
        birth_place=data.get("birth_place", "—"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        timezone=data.get("timezone"),
    )

    kb = webapp_keyboard() or main_menu_keyboard()
    await message.answer(texts.PROFILE_SAVED, reply_markup=kb)
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())
