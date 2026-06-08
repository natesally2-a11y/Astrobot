from datetime import date, time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology import AIInterpreter, ChartCalculator, ChartRenderer
from app.bot.keyboards.inline import (
    GDPR_TEXT,
    city_keyboard,
    day_keyboard,
    gdpr_keyboard,
    hour_keyboard,
    main_menu_keyboard,
    minute_keyboard,
    month_keyboard,
    year_keyboard,
)
from app.bot.states import RegistrationStates
from app.bot.utils.geocoding import estimate_timezone, timezone_to_offset
from app.database import crud

router = Router()
calculator = ChartCalculator()
ai = AIInterpreter()
renderer = ChartRenderer()


@router.callback_query(F.data == "start_registration")
async def start_registration(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RegistrationStates.waiting_birth_date)
    await callback.message.edit_text(
        "📅 Выберите год рождения:",
        reply_markup=year_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_year")
async def back_to_year(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RegistrationStates.waiting_birth_date)
    await callback.message.edit_text("📅 Выберите год рождения:", reply_markup=year_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("year_"))
async def select_year(callback: CallbackQuery, state: FSMContext) -> None:
    year = int(callback.data.split("_")[1])
    await state.update_data(birth_year=year)
    await callback.message.edit_text(
        f"📅 Выберите месяц ({year}):",
        reply_markup=month_keyboard(year),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("month_"))
async def select_month(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("_")
    year, month = int(parts[1]), int(parts[2])
    await state.update_data(birth_month=month)
    await callback.message.edit_text(
        f"📅 Выберите день ({month:02d}.{year}):",
        reply_markup=day_keyboard(year, month),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("day_"))
async def select_day(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("_")
    year, month, day = int(parts[1]), int(parts[2]), int(parts[3])
    await state.update_data(birth_day=day, birth_date=date(year, month, day))
    await state.set_state(RegistrationStates.waiting_birth_time)
    await callback.message.edit_text(
        "⏰ Выберите час рождения:\n\n"
        "💡 Точное время важно для расчёта Асцендента и домов. "
        "Если не знаете — выберите «Не знаю» (будет использовано полдень).",
        reply_markup=hour_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_date")
async def back_to_date(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    year = data.get("birth_year", 1990)
    month = data.get("birth_month", 1)
    await state.set_state(RegistrationStates.waiting_birth_date)
    await callback.message.edit_text(
        f"📅 Выберите день ({month:02d}.{year}):",
        reply_markup=day_keyboard(year, month),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_hour")
async def back_to_hour(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RegistrationStates.waiting_birth_time)
    await callback.message.edit_text(
        "⏰ Выберите час рождения:",
        reply_markup=hour_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hour_"))
async def select_hour(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data == "hour_unknown":
        await state.update_data(birth_time=None)
        await state.set_state(RegistrationStates.waiting_birth_place)
        await callback.message.edit_text(
            "📍 Введите город рождения (на русском или английском):",
        )
        await callback.answer()
        return

    hour = int(callback.data.split("_")[1])
    await state.update_data(birth_hour=hour)
    await callback.message.edit_text(
        f"⏰ Выберите минуты ({hour:02d}:??):",
        reply_markup=minute_keyboard(hour),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("time_"))
async def select_time(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("_")
    hour, minute = int(parts[1]), int(parts[2])
    await state.update_data(birth_time=time(hour, minute))
    await state.set_state(RegistrationStates.waiting_birth_place)
    await callback.message.edit_text("📍 Введите город рождения (на русском или английском):")
    await callback.answer()


@router.message(RegistrationStates.waiting_birth_place)
async def process_birth_place(message: Message, state: FSMContext) -> None:
    from app.bot.utils.geocoding import search_cities

    place = message.text.strip()
    await message.answer("🔍 Ищу город...")
    results = await search_cities(place)
    if not results:
        await message.answer("❌ Город не найден. Попробуйте другое название:")
        return
    await state.update_data(city_results=results)
    await state.set_state(RegistrationStates.waiting_place_confirm)
    await message.answer("📍 Выберите город из списка:", reply_markup=city_keyboard(results))


@router.callback_query(F.data.startswith("city_"))
async def confirm_city(callback: CallbackQuery, state: FSMContext) -> None:
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    cities = data.get("city_results", [])
    if idx >= len(cities):
        await callback.answer("Ошибка выбора города")
        return

    city = cities[idx]
    tz = estimate_timezone(city["longitude"])
    await state.update_data(
        birth_place=city["short_name"],
        latitude=city["latitude"],
        longitude=city["longitude"],
        timezone=tz,
    )
    await state.set_state(RegistrationStates.waiting_gdpr_consent)
    await callback.message.edit_text(GDPR_TEXT, reply_markup=gdpr_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cancel_registration")
async def cancel_registration(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Регистрация отменена. Используйте /start для начала.")
    await callback.answer()


@router.callback_query(F.data == "gdpr_accept")
async def gdpr_accept(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    user = await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        first_name=callback.from_user.first_name,
        username=callback.from_user.username,
    )
    await crud.set_gdpr_consent(session, user)

    birth_date = data["birth_date"]
    birth_time = data.get("birth_time")
    tz_offset = timezone_to_offset(data.get("timezone", "UTC+3"))

    await crud.save_birth_data(
        session,
        user_id=user.telegram_id,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place=data["birth_place"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        tz_name=data.get("timezone", "UTC+3"),
    )

    chart = calculator.calculate_natal_chart(
        birth_date, birth_time, data["latitude"], data["longitude"], tz_offset
    )
    analysis = await ai.interpret_natal(chart, callback.from_user.first_name or "друг")
    await crud.save_reading(session, user.telegram_id, "natal", None, analysis)

    await state.clear()
    await callback.message.answer(
        f"✅ Ваша натальная карта создана!\n"
        f"🌟 Асцендент: {chart.ascendant_sign}\n\n"
        f"Откройте Mini App для интерактивной визуализации карты.",
    )
    await callback.message.answer(analysis, reply_markup=main_menu_keyboard())
    await callback.answer()
