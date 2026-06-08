"""
/today command handler — Personalized daily forecast.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database import crud
from app.database.models import User
from app.astrology.calculations import NatalChart, get_current_transits
from app.astrology.ai_interpreter import get_daily_forecast
from app.bot.keyboards.inline import get_main_menu_keyboard

router = Router(name="today")


@router.message(Command("today"))
async def cmd_today(message: Message, session=None, db_user: Optional[User] = None):
    await send_today(message, session, message.from_user.id, db_user)


async def send_today(message: Message, session, user_id: int, db_user: Optional[User] = None):
    if session is None:
        await message.answer("⚠️ Ошибка подключения к базе данных.")
        return

    birth_data = await crud.get_birth_data(session, user_id)
    if not birth_data:
        await message.answer(
            "❌ Данные рождения не найдены.\n"
            "Используйте /start для регистрации.",
        )
        return

    user = db_user or await crud.get_user(session, user_id)
    user_name = user.display_name if user else "Пользователь"
    is_pro = user.is_pro if user else False

    msg = await message.answer("☀️ Составляю ваш прогноз на сегодня...")

    try:
        chart = NatalChart(
            birth_date=birth_data.birth_date,
            birth_time=birth_data.birth_time,
            latitude=float(birth_data.latitude or 55.75),
            longitude=float(birth_data.longitude or 37.62),
            timezone=birth_data.timezone or "Europe/Moscow",
        )

        transit_chart = None
        if is_pro:
            transit_chart = get_current_transits(chart)

        today_str = date.today().strftime("%d.%m.%Y")
        forecast = await get_daily_forecast(chart, user_name, transit_chart)

        await crud.save_reading(session, user_id, "daily", None, forecast)

        await msg.delete()

        extra = ""
        if not is_pro:
            extra = "\n\n💡 <i>Оформите Pro (50⭐/мес) для расширенных прогнозов с учётом транзитов.</i>"

        await message.answer(
            f"☀️ <b>Прогноз на {today_str}</b>\n"
            f"Для {user_name}\n\n"
            f"{forecast}{extra}",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(has_birth_data=True, is_pro=is_pro),
        )

    except Exception as e:
        await msg.delete()
        await message.answer("❌ Ошибка при составлении прогноза. Попробуйте позже.")
