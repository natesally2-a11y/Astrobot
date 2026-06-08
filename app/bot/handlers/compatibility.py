"""Handler for /compatibility — synastry analysis."""

from datetime import date, time
from decimal import Decimal

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.database.crud import (
    get_user_with_birth_data,
    check_subscription_level,
    check_daily_limit,
    increment_daily_questions,
    save_reading,
)
from app.astrology.calculations import calculate_natal_chart
from app.astrology.ai_interpreter import interpret_compatibility
from app.bot.keyboards.inline import compatibility_input_keyboard, subscription_keyboard
from app.bot.handlers.start import OnboardingStates
from app.bot.utils.geocoding import geocode_city
from app.config import settings

router = Router()


@router.message(Command("compatibility"))
async def cmd_compatibility(message: Message):
    if not message.from_user:
        return

    user = await get_user_with_birth_data(message.from_user.id)
    if not user or not user.birth_data:
        await message.answer("❌ Сначала введите свои данные рождения: /start")
        return

    level = await check_subscription_level(message.from_user.id)

    if level == "free":
        can_ask, remaining = await check_daily_limit(
            message.from_user.id, settings.free_daily_questions
        )
        if not can_ask:
            await message.answer(
                "⚠️ Лимит бесплатных запросов исчерпан.\n"
                "Подпишитесь для безлимитного доступа:",
                reply_markup=subscription_keyboard(),
            )
            return

    await message.answer(
        "💕 <b>Анализ совместимости</b>\n\n"
        "Для анализа синастрии нужны данные второго человека.\n"
        "Введите дату рождения партнёра в формате <b>ДД.ММ.ГГГГ</b>\n"
        "(например: 15.03.1995):",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "compat_start")
async def compat_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💕 Введите дату рождения партнёра в формате <b>ДД.ММ.ГГГГ</b>:",
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.compat_date)
    await callback.answer()


@router.message(OnboardingStates.compat_date)
async def process_compat_date(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        parts = text.replace("/", ".").replace("-", ".").split(".")
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])
        date(year, month, day)
    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат. Введите дату как <b>ДД.ММ.ГГГГ</b>:", parse_mode="HTML")
        return

    await state.update_data(compat_year=year, compat_month=month, compat_day=day)
    await message.answer(
        "⏰ Введите время рождения партнёра (<b>ЧЧ:ММ</b>) или напишите «нет»:",
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.compat_time)


@router.message(OnboardingStates.compat_time)
async def process_compat_time(message: Message, state: FSMContext):
    text = message.text.strip().lower() if message.text else ""
    hour, minute = 12, 0

    if text not in ("нет", "не знаю", "no", "-"):
        try:
            parts = text.replace(".", ":").replace("-", ":").split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except (ValueError, IndexError):
            await message.answer("❌ Введите время как <b>ЧЧ:ММ</b> или напишите «нет»:", parse_mode="HTML")
            return

    await state.update_data(compat_hour=hour, compat_minute=minute)
    await message.answer("📍 Введите город рождения партнёра:")
    await state.set_state(OnboardingStates.compat_city)


@router.message(OnboardingStates.compat_city)
async def process_compat_city(message: Message, state: FSMContext):
    city = message.text.strip() if message.text else ""
    if len(city) < 2:
        await message.answer("❌ Введите название города:")
        return

    await message.answer("🔍 Ищу город...")
    geo = await geocode_city(city)
    if not geo:
        await message.answer("❌ Город не найден. Попробуйте другое название:")
        return

    data = await state.get_data()
    await state.clear()

    user = await get_user_with_birth_data(message.from_user.id)
    if not user or not user.birth_data:
        await message.answer("❌ Ваши данные рождения не найдены. Используйте /start")
        return

    bd = user.birth_data
    chart1 = calculate_natal_chart(
        birth_date=bd.birth_date,
        birth_time=bd.birth_time,
        latitude=float(bd.latitude) if bd.latitude else 55.7558,
        longitude=float(bd.longitude) if bd.longitude else 37.6173,
    )

    compat_date = date(data["compat_year"], data["compat_month"], data["compat_day"])
    compat_time = time(data.get("compat_hour", 12), data.get("compat_minute", 0))
    chart2 = calculate_natal_chart(
        birth_date=compat_date,
        birth_time=compat_time,
        latitude=geo["latitude"],
        longitude=geo["longitude"],
    )

    await message.answer("🔮 Анализирую совместимость...")

    result = await interpret_compatibility(
        chart1, chart2,
        name1=user.first_name or "Вы",
        name2="Партнёр",
    )
    await message.answer(result, parse_mode="Markdown")

    level = await check_subscription_level(message.from_user.id)
    if level == "free":
        await increment_daily_questions(message.from_user.id)

    await save_reading(
        user_id=message.from_user.id,
        reading_type="compatibility",
        ai_response=result,
    )
