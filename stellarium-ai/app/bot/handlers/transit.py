"""
/transit command handler — Transit analysis (Pro feature).
"""
from __future__ import annotations

from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database import crud
from app.database.models import User
from app.astrology.calculations import NatalChart, get_current_transits
from app.astrology.ai_interpreter import get_transit_forecast
from app.bot.keyboards.inline import get_main_menu_keyboard, get_subscription_keyboard

router = Router(name="transit")


@router.message(Command("transit"))
async def cmd_transit(message: Message, session=None, db_user: Optional[User] = None):
    await send_transit(message, session, message.from_user.id, db_user)


async def send_transit(message: Message, session, user_id: int, db_user: Optional[User] = None):
    if session is None:
        await message.answer("⚠️ Ошибка подключения к базе данных.")
        return

    user = db_user or await crud.get_user(session, user_id)
    if not user or not user.is_pro:
        await message.answer(
            "💫 <b>Анализ транзитов доступен в Stellarium Pro</b>\n\n"
            "Узнайте какие планеты влияют на вашу жизнь прямо сейчас!\n\n"
            "За 50 Telegram Stars в месяц:",
            parse_mode="HTML",
            reply_markup=get_subscription_keyboard(),
        )
        return

    birth_data = await crud.get_birth_data(session, user_id)
    if not birth_data:
        await message.answer("❌ Данные рождения не найдены. Используйте /start.")
        return

    user_name = user.display_name
    msg = await message.answer("💫 Анализирую текущие транзиты...")

    try:
        natal_chart = NatalChart(
            birth_date=birth_data.birth_date,
            birth_time=birth_data.birth_time,
            latitude=float(birth_data.latitude or 55.75),
            longitude=float(birth_data.longitude or 37.62),
            timezone=birth_data.timezone or "Europe/Moscow",
        )

        transit_chart = get_current_transits(natal_chart)
        forecast = await get_transit_forecast(natal_chart, user_name, transit_chart)
        await crud.save_reading(session, user_id, "transit", None, forecast)

        transit_summary = _format_transit_summary(transit_chart)

        await msg.delete()
        await message.answer(
            f"💫 <b>Текущие транзиты</b>\nДля {user_name}\n\n"
            f"{transit_summary}\n\n"
            f"{forecast}",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(has_birth_data=True, is_pro=True),
        )
    except Exception:
        await msg.delete()
        await message.answer("❌ Ошибка при анализе транзитов. Попробуйте позже.")


def _format_transit_summary(transit_chart: NatalChart) -> str:
    from app.astrology.calculations import PLANET_NAMES_RU, PLANET_SYMBOLS
    lines = ["<b>Планеты сейчас:</b>"]
    for name in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
        planet = transit_chart.planets.get(name)
        if planet:
            symbol = PLANET_SYMBOLS.get(name, "")
            lines.append(f"{symbol} {PLANET_NAMES_RU.get(name, name)}: {planet.sign_symbol}{planet.sign_ru}")
    return "\n".join(lines)
