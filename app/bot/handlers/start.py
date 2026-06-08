from __future__ import annotations

from datetime import date, time

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.keyboards.calendar import hour_keyboard, minute_keyboard, month_calendar_keyboard, starting_calendar
from app.bot.keyboards.consent import gdpr_consent_keyboard, onboarding_start_keyboard
from app.bot.texts import GDPR_CONSENT_TEXT, WELCOME_TEXT
from app.bot.utils.geocoding import search_city
from app.database.crud import get_or_create_user, save_birth_data, set_gdpr_consent
from app.database.session import AsyncSessionLocal

router = Router(name="start")


class OnboardingStates(StatesGroup):
    birth_date = State()
    birth_time_hour = State()
    birth_time_minute = State()
    birth_place = State()
    gdpr = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with AsyncSessionLocal() as session:
        await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
        )
    await message.answer(WELCOME_TEXT, reply_markup=onboarding_start_keyboard())


@router.callback_query(F.data == "onboarding:start")
async def onboarding_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.birth_date)
    await callback.message.answer("Выберите дату рождения:", reply_markup=starting_calendar())
    await callback.answer()


@router.callback_query(F.data.startswith("calendar:"))
async def calendar_switch(callback: CallbackQuery) -> None:
    _, year, month = callback.data.split(":")
    markup = month_calendar_keyboard(int(year), int(month))
    await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(OnboardingStates.birth_date, F.data.startswith("birthdate:"))
async def set_birth_date(callback: CallbackQuery, state: FSMContext) -> None:
    _, value = callback.data.split(":")
    await state.update_data(birth_date=value)
    await state.set_state(OnboardingStates.birth_time_hour)
    await callback.message.answer(
        "Выберите час рождения. Точность времени влияет на дома и аспекты:",
        reply_markup=hour_keyboard(),
    )
    await callback.answer("Дата сохранена")


@router.callback_query(OnboardingStates.birth_time_hour, F.data.startswith("hour:"))
async def set_birth_hour(callback: CallbackQuery, state: FSMContext) -> None:
    _, value = callback.data.split(":")
    if value == "unknown":
        await state.update_data(birth_time=None)
        await state.set_state(OnboardingStates.birth_place)
        await callback.message.answer("Введите место рождения (город):")
        await callback.answer("Сохранили без точного времени")
        return

    await state.update_data(selected_hour=value)
    await state.set_state(OnboardingStates.birth_time_minute)
    await callback.message.answer("Выберите минуты:", reply_markup=minute_keyboard(value))
    await callback.answer()


@router.callback_query(OnboardingStates.birth_time_minute, F.data == "time:back")
async def time_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.birth_time_hour)
    await callback.message.answer("Выберите час рождения:", reply_markup=hour_keyboard())
    await callback.answer()


@router.callback_query(OnboardingStates.birth_time_minute, F.data.startswith("time:"))
async def set_birth_minutes(callback: CallbackQuery, state: FSMContext) -> None:
    _, hour, minute = callback.data.split(":")
    await state.update_data(birth_time=f"{hour}:{minute}")
    await state.set_state(OnboardingStates.birth_place)
    await callback.message.answer("Введите место рождения (город):")
    await callback.answer("Время сохранено")


@router.message(OnboardingStates.birth_place)
async def set_birth_place(message: Message, state: FSMContext) -> None:
    try:
        options = await search_city(message.text)
    except Exception:
        await message.answer("Сервис геопоиска временно недоступен. Попробуйте чуть позже.")
        return
    if not options:
        await message.answer("Город не найден. Попробуйте формат: «Москва» или «Moscow, Russia».")
        return

    await state.update_data(place_options=options)
    rows = [
        [InlineKeyboardButton(text=city["display_name"][:64], callback_data=f"place:{idx}")]
        for idx, city in enumerate(options)
    ]
    await message.answer(
        "Выберите подходящий город:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(OnboardingStates.birth_place, F.data.startswith("place:"))
async def pick_place(callback: CallbackQuery, state: FSMContext) -> None:
    _, index = callback.data.split(":")
    data = await state.get_data()
    options = data.get("place_options", [])
    selected = options[int(index)]
    await state.update_data(
        birth_place=selected["display_name"],
        latitude=selected["lat"],
        longitude=selected["lon"],
        timezone=selected.get("timezone"),
    )
    await state.set_state(OnboardingStates.gdpr)
    await callback.message.answer(GDPR_CONSENT_TEXT, reply_markup=gdpr_consent_keyboard())
    await callback.answer()


@router.callback_query(OnboardingStates.gdpr, F.data == "gdpr:privacy")
async def gdpr_privacy(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Политика конфиденциальности: используйте команду /privacy для полного текста."
    )
    await callback.answer()


@router.callback_query(OnboardingStates.gdpr, F.data == "gdpr:agree")
async def gdpr_agree(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    birth_date = date.fromisoformat(data["birth_date"])
    birth_time = time.fromisoformat(data["birth_time"]) if data.get("birth_time") else None

    async with AsyncSessionLocal() as session:
        await save_birth_data(
            session=session,
            user_id=callback.from_user.id,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=data["birth_place"],
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            timezone=data.get("timezone"),
        )
        await set_gdpr_consent(session, callback.from_user.id, True)

    await state.clear()
    await callback.message.answer(
        "✅ Натальная карта создана. Используйте /chart для просмотра и /today для прогноза."
    )
    await callback.answer("Согласие принято")

