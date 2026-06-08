"""
/chart command handler — Show natal chart with AI interpretation.
"""
from __future__ import annotations

import io
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from app.database import crud
from app.database.models import User
from app.astrology.calculations import NatalChart
from app.astrology.ai_interpreter import get_natal_interpretation
from app.astrology.chart_renderer import render_natal_chart_svg
from app.bot.keyboards.inline import get_main_menu_keyboard

router = Router(name="chart")

PLANETS_ORDER = ["Sun", "Moon", "Mercury", "Venus", "Mars",
                 "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]


@router.message(Command("chart"))
async def cmd_chart(message: Message, session=None, db_user: Optional[User] = None):
    await send_chart(message, session, message.from_user.id, db_user)


async def send_chart(message: Message, session, user_id: int, db_user: Optional[User] = None):
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

    msg = await message.answer("🔮 Рассчитываю вашу натальную карту...")

    try:
        chart = NatalChart(
            birth_date=birth_data.birth_date,
            birth_time=birth_data.birth_time,
            latitude=float(birth_data.latitude or 55.75),
            longitude=float(birth_data.longitude or 37.62),
            timezone=birth_data.timezone or "Europe/Moscow",
        )

        svg_content = render_natal_chart_svg(chart, f"Карта {user_name}")
        svg_bytes = svg_content.encode("utf-8")
        svg_file = BufferedInputFile(svg_bytes, filename="natal_chart.svg")

        planets_text = _format_planets(chart)

        await msg.delete()
        await message.answer_document(
            svg_file,
            caption=f"🗺 <b>Натальная карта — {user_name}</b>\n\n{planets_text}",
            parse_mode="HTML",
        )

        await message.answer("🤖 Анализирую вашу карту с помощью ИИ...")
        interpretation = await get_natal_interpretation(chart, user_name)

        await crud.save_reading(session, user_id, "natal", None, interpretation)

        await message.answer(
            f"✨ <b>Интерпретация карты</b>\n\n{interpretation}",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(has_birth_data=True, is_pro=user.is_pro if user else False),
        )

    except Exception as e:
        await msg.delete()
        await message.answer(
            "❌ Произошла ошибка при расчёте карты. Попробуйте позже.",
        )


def _format_planets(chart: NatalChart) -> str:
    from app.astrology.calculations import PLANET_NAMES_RU, PLANET_SYMBOLS
    lines = ["<b>Планеты в знаках:</b>"]
    for name in PLANETS_ORDER:
        planet = chart.planets.get(name)
        if planet:
            symbol = PLANET_SYMBOLS.get(name, "")
            retro = " ℞" if planet.retrograde else ""
            lines.append(
                f"{symbol} <b>{PLANET_NAMES_RU.get(name, name)}:</b> "
                f"{planet.sign_symbol}{planet.sign_ru} {int(planet.degree)}°{retro}"
            )

    if chart.ascendant > 0:
        from app.astrology.calculations import ZODIAC_SIGNS, ZODIAC_SYMBOLS
        asc_sign_num = int(chart.ascendant / 30) % 12
        lines.append(
            f"↑ <b>Асцендент:</b> {ZODIAC_SYMBOLS[asc_sign_num]}{ZODIAC_SIGNS[asc_sign_num]}"
        )

    if chart.aspects:
        lines.append("\n<b>Главные аспекты:</b>")
        for aspect in chart.aspects[:5]:
            sym1 = PLANET_SYMBOLS.get(aspect.planet1, "")
            sym2 = PLANET_SYMBOLS.get(aspect.planet2, "")
            lines.append(f"{sym1}—{aspect.aspect_name}—{sym2} (орб {aspect.orb:.1f}°)")

    return "\n".join(lines)
