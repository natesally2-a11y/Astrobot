"""Handler for /transit — current transit analysis (Premium)."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.crud import (
    get_user_with_birth_data,
    check_subscription_level,
    save_reading,
)
from app.astrology.calculations import (
    calculate_natal_chart,
    get_current_transits,
    calculate_transit_aspects,
    format_transits_text,
)
from app.astrology.ai_interpreter import interpret_transits
from app.bot.keyboards.inline import subscription_keyboard

router = Router()


@router.message(Command("transit"))
async def cmd_transit(message: Message):
    if not message.from_user:
        return

    level = await check_subscription_level(message.from_user.id)
    if level == "free":
        await message.answer(
            "⭐ Подробный анализ транзитов доступен подписчикам "
            "<b>Stellarium Pro</b> и выше.\n\n"
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
    chart = calculate_natal_chart(
        birth_date=bd.birth_date,
        birth_time=bd.birth_time,
        latitude=float(bd.latitude) if bd.latitude else 55.7558,
        longitude=float(bd.longitude) if bd.longitude else 37.6173,
    )

    transits = get_current_transits()
    transit_aspects = calculate_transit_aspects(chart.planets, transits)
    transits_text = format_transits_text(chart, transits, transit_aspects)

    await message.answer(transits_text)

    await message.answer("🤖 Анализирую транзиты...")
    interpretation = await interpret_transits(chart, user_name=user.first_name or "")
    await message.answer(interpretation, parse_mode="Markdown")

    await save_reading(
        user_id=message.from_user.id,
        reading_type="transit",
        ai_response=interpretation,
    )
