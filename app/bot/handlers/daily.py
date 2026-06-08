"""Handlers for /today and /week forecasts."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.crud import (
    get_user_with_birth_data,
    check_daily_limit,
    increment_daily_questions,
    check_subscription_level,
    save_reading,
)
from app.astrology.calculations import calculate_natal_chart
from app.astrology.ai_interpreter import interpret_daily_forecast, interpret_weekly_forecast
from app.bot.keyboards.inline import subscription_keyboard
from app.config import settings

router = Router()


@router.message(Command("today"))
async def cmd_today(message: Message):
    if not message.from_user:
        return

    user = await get_user_with_birth_data(message.from_user.id)
    if not user or not user.birth_data:
        await message.answer("❌ Сначала введите данные рождения: /start")
        return

    level = await check_subscription_level(message.from_user.id)
    detailed = level in ("pro", "oracle")

    if level == "free":
        can_ask, remaining = await check_daily_limit(
            message.from_user.id, settings.free_daily_questions
        )
        if not can_ask:
            await message.answer(
                "⚠️ Вы исчерпали бесплатные запросы на сегодня.\n\n"
                "Обновите подписку для безлимитного доступа:",
                reply_markup=subscription_keyboard(),
            )
            return

    bd = user.birth_data
    await message.answer("🔮 Составляю персональный прогноз...")

    chart = calculate_natal_chart(
        birth_date=bd.birth_date,
        birth_time=bd.birth_time,
        latitude=float(bd.latitude) if bd.latitude else 55.7558,
        longitude=float(bd.longitude) if bd.longitude else 37.6173,
    )

    forecast = await interpret_daily_forecast(
        chart, user_name=user.first_name or "", detailed=detailed
    )
    await message.answer(forecast, parse_mode="Markdown")

    if level == "free":
        await increment_daily_questions(message.from_user.id)
        _, remaining = await check_daily_limit(
            message.from_user.id, settings.free_daily_questions
        )
        await message.answer(
            f"ℹ️ Осталось бесплатных запросов сегодня: {remaining}/{settings.free_daily_questions}"
        )

    await save_reading(
        user_id=message.from_user.id,
        reading_type="daily",
        ai_response=forecast,
    )


@router.message(Command("week"))
async def cmd_week(message: Message):
    if not message.from_user:
        return

    level = await check_subscription_level(message.from_user.id)
    if level == "free":
        await message.answer(
            "⭐ Недельный прогноз доступен подписчикам <b>Stellarium Pro</b> и выше.\n\n"
            "Оформите подписку:",
            reply_markup=subscription_keyboard(),
            parse_mode="HTML",
        )
        return

    user = await get_user_with_birth_data(message.from_user.id)
    if not user or not user.birth_data:
        await message.answer("❌ Сначала введите данные рождения: /start")
        return

    bd = user.birth_data
    await message.answer("🔮 Составляю прогноз на неделю...")

    chart = calculate_natal_chart(
        birth_date=bd.birth_date,
        birth_time=bd.birth_time,
        latitude=float(bd.latitude) if bd.latitude else 55.7558,
        longitude=float(bd.longitude) if bd.longitude else 37.6173,
    )

    forecast = await interpret_weekly_forecast(chart, user_name=user.first_name or "")
    await message.answer(forecast, parse_mode="Markdown")

    await save_reading(
        user_id=message.from_user.id,
        reading_type="weekly",
        ai_response=forecast,
    )
