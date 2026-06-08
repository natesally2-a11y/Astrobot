from __future__ import annotations

from datetime import date, time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.astrology.calculations import calculate_natal_chart
from app.bot.keyboards.onboarding import (
    consent_keyboard,
    day_keyboard,
    hour_keyboard,
    minute_keyboard,
    month_keyboard,
    year_keyboard,
)
from app.bot.states import OnboardingState
from app.bot.utils.formatters import chart_preview_text
from app.config import GDPR_CONSENT_TEXT
from app.database.crud import create_or_update_user, get_user, set_gdpr_consent, upsert_birth_data
from app.database.session import AsyncSessionLocal
from app.services.geocoding import GeocodingService


router = Router(name="onboarding")
geocoder = GeocodingService()


def _build_location_choice_keyboard(locations: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, location in enumerate(locations):
        builder.button(
            text=location["display_name"][:60],
            callback_data=f"place:choose:{index}",
        )
    builder.button(text="Попробовать другой город", callback_data="place:retry")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data == "onboarding:start")
async def start_onboarding(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    async with AsyncSessionLocal() as session:
        user = await get_user(session, callback.from_user.id)
        if user is None:
            await create_or_update_user(
                session,
                telegram_id=callback.from_user.id,
                first_name=callback.from_user.first_name,
                username=callback.from_user.username,
            )
            user = await get_user(session, callback.from_user.id)

    if user and user.gdpr_consent:
        await state.set_state(OnboardingState.waiting_for_year)
        await callback.message.answer("Выберите год рождения:", reply_markup=year_keyboard())
    else:
        await state.set_state(OnboardingState.waiting_for_consent)
        await callback.message.answer(GDPR_CONSENT_TEXT, reply_markup=consent_keyboard())
    await callback.answer()


@router.callback_query(F.data == "consent:agree")
async def consent_agree(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    async with AsyncSessionLocal() as session:
        await set_gdpr_consent(session, callback.from_user.id, True)

    await state.set_state(OnboardingState.waiting_for_year)
    await callback.message.answer("Спасибо. Теперь выберите год рождения:", reply_markup=year_keyboard())
    await callback.answer("Согласие сохранено")


@router.callback_query(F.data.startswith("date:page:"))
async def navigate_year_page(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[2])
    await callback.message.edit_reply_markup(reply_markup=year_keyboard(page))
    await callback.answer()


@router.callback_query(F.data.startswith("date:year:"))
async def pick_year(callback: CallbackQuery, state: FSMContext) -> None:
    year = int(callback.data.split(":")[2])
    await state.update_data(year=year)
    await state.set_state(OnboardingState.waiting_for_month)
    await callback.message.answer(
        f"Год: {year}. Теперь выберите месяц:",
        reply_markup=month_keyboard(year),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("date:month:"))
async def pick_month(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, year, month = callback.data.split(":")
    year_value = int(year)
    month_value = int(month)
    await state.update_data(year=year_value, month=month_value)
    await state.set_state(OnboardingState.waiting_for_day)
    await callback.message.answer(
        f"Дата: {year_value}-{month_value:02d}. Теперь выберите день:",
        reply_markup=day_keyboard(year_value, month_value),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("date:day:"))
async def pick_day(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, year, month, day = callback.data.split(":")
    await state.update_data(year=int(year), month=int(month), day=int(day))
    await state.set_state(OnboardingState.waiting_for_hour)
    await callback.message.answer("Выберите час рождения:", reply_markup=hour_keyboard())
    await callback.answer()


@router.callback_query(F.data == "date:back:year")
async def back_to_year(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OnboardingState.waiting_for_year)
    await callback.message.answer("Выберите год рождения:", reply_markup=year_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("date:back:month:"))
async def back_to_month(callback: CallbackQuery, state: FSMContext) -> None:
    year = int(callback.data.split(":")[3])
    await state.set_state(OnboardingState.waiting_for_month)
    await callback.message.answer("Выберите месяц рождения:", reply_markup=month_keyboard(year))
    await callback.answer()


@router.callback_query(F.data.startswith("time:hour:"))
async def pick_hour(callback: CallbackQuery, state: FSMContext) -> None:
    hour = int(callback.data.split(":")[2])
    await state.update_data(hour=hour)
    await state.set_state(OnboardingState.waiting_for_minute)
    await callback.message.answer(
        f"Час: {hour:02d}. Теперь выберите минуты:",
        reply_markup=minute_keyboard(hour),
    )
    await callback.answer()


@router.callback_query(F.data == "time:approx")
async def pick_approximate_time(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(hour=12, minute=0, is_time_approximate=True)
    await state.set_state(OnboardingState.waiting_for_place_query)
    await callback.message.answer(
        "Сохраняем время как примерное 12:00. Теперь напишите город рождения."
    )
    await callback.answer()


@router.callback_query(F.data.startswith("time:minute:"))
async def pick_minute(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, hour, minute = callback.data.split(":")
    await state.update_data(
        hour=int(hour),
        minute=int(minute),
        is_time_approximate=False,
    )
    await state.set_state(OnboardingState.waiting_for_place_query)
    await callback.message.answer("Отлично. Теперь напишите город рождения.")
    await callback.answer()


@router.callback_query(F.data == "time:back:hour")
async def back_to_hour(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OnboardingState.waiting_for_hour)
    await callback.message.answer("Выберите час рождения:", reply_markup=hour_keyboard())
    await callback.answer()


@router.message(OnboardingState.waiting_for_place_query)
async def receive_place_query(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, отправьте город текстом.")
        return

    locations = await geocoder.search_city(message.text)
    if not locations:
        await message.answer("Не нашел город. Попробуйте другой вариант написания.")
        return

    serialized = [
        {
            "display_name": item.display_name,
            "latitude": item.latitude,
            "longitude": item.longitude,
            "timezone": item.timezone,
            "raw": item.raw,
        }
        for item in locations
    ]
    await state.update_data(locations=serialized)
    await state.set_state(OnboardingState.waiting_for_place_choice)
    await message.answer(
        "Выберите подходящий вариант:",
        reply_markup=_build_location_choice_keyboard(serialized),
    )


@router.callback_query(F.data == "place:retry")
async def retry_place(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OnboardingState.waiting_for_place_query)
    await callback.message.answer("Напишите город рождения еще раз.")
    await callback.answer()


@router.callback_query(F.data.startswith("place:choose:"))
async def choose_place(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    index = int(callback.data.split(":")[2])
    data = await state.get_data()
    locations = data.get("locations", [])
    if index >= len(locations):
        await callback.answer("Вариант устарел, попробуйте снова", show_alert=True)
        return

    location = locations[index]
    birth_date = date(data["year"], data["month"], data["day"])
    birth_time = time(data.get("hour", 12), data.get("minute", 0))
    is_time_approximate = bool(data.get("is_time_approximate", False))

    async with AsyncSessionLocal() as session:
        await upsert_birth_data(
            session=session,
            telegram_id=callback.from_user.id,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=location["display_name"],
            latitude=location["latitude"],
            longitude=location["longitude"],
            timezone=location["timezone"],
            is_time_approximate=is_time_approximate,
            raw_geocoding_payload=location["raw"],
        )

    chart = calculate_natal_chart(
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place=location["display_name"],
        latitude=location["latitude"],
        longitude=location["longitude"],
        timezone_name=location["timezone"],
    )
    await callback.message.answer(chart_preview_text(chart))
    await state.clear()
    await callback.answer("Карта сохранена")


@router.callback_query(F.data == "onboarding:cancel")
async def cancel_onboarding(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Онбординг остановлен. Вернуться можно командой /start.")
    await callback.answer("Отменено")
