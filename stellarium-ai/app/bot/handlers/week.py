"""
/week command handler — Weekly forecast (Pro feature).
"""
from __future__ import annotations

from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database import crud
from app.database.models import User
from app.astrology.calculations import NatalChart
from app.astrology.ai_interpreter import get_weekly_forecast
from app.bot.keyboards.inline import get_main_menu_keyboard, get_subscription_keyboard

router = Router(name="week")


@router.message(Command("week"))
async def cmd_week(message: Message, session=None, db_user: Optional[User] = None):
    await send_week(message, session, message.from_user.id, db_user)


async def send_week(message: Message, session, user_id: int, db_user: Optional[User] = None):
    if session is None:
        await message.answer("⚠️ Ошибка подключения к базе данных.")
        return

    user = db_user or await crud.get_user(session, user_id)
    if not user or not user.is_pro:
        await message.answer(
            "⭐ <b>Недельные прогнозы доступны в Stellarium Pro</b>\n\n"
            "За 50 Telegram Stars в месяц вы получите:\n"
            "• Подробные ежедневные прогнозы\n"
            "• Недельные и месячные прогнозы\n"
            "• Анализ совместимости (до 3 партнёров)\n"
            "• Безлимитные вопросы ИИ",
            parse_mode="HTML",
            reply_markup=get_subscription_keyboard(),
        )
        return

    birth_data = await crud.get_birth_data(session, user_id)
    if not birth_data:
        await message.answer("❌ Данные рождения не найдены. Используйте /start.")
        return

    user_name = user.display_name

    msg = await message.answer("📅 Составляю прогноз на неделю...")

    try:
        chart = NatalChart(
            birth_date=birth_data.birth_date,
            birth_time=birth_data.birth_time,
            latitude=float(birth_data.latitude or 55.75),
            longitude=float(birth_data.longitude or 37.62),
            timezone=birth_data.timezone or "Europe/Moscow",
        )

        forecast = await get_weekly_forecast(chart, user_name)
        await crud.save_reading(session, user_id, "weekly", None, forecast)

        await msg.delete()
        await message.answer(
            f"📅 <b>Прогноз на неделю</b>\nДля {user_name}\n\n{forecast}",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(has_birth_data=True, is_pro=True),
        )
    except Exception:
        await msg.delete()
        await message.answer("❌ Ошибка при составлении прогноза. Попробуйте позже.")
