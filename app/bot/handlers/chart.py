"""Natal chart handlers (/chart)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import interpret_natal_chart
from app.astrology.calculations import compute_chart
from app.astrology.chart_renderer import render_svg
from app.bot.utils.access import ensure_birth_data, ensure_consent
from app.config import get_settings
from app.database.crud import add_reading
from app.database.models import User

router = Router(name="chart")


@router.message(Command("chart"))
async def cmd_chart(message: Message, session: AsyncSession, user: User) -> None:
    if not await ensure_consent(user, message):
        return
    bd = await ensure_birth_data(user, session, message)
    if bd is None:
        return

    placeholder = await message.answer("✨ Строю вашу натальную карту…")

    chart = compute_chart(
        birth_date=bd.birth_date,
        birth_time=None if bd.time_is_unknown else bd.birth_time,
        latitude=float(bd.latitude),
        longitude=float(bd.longitude),
        timezone_name=bd.timezone,
    )
    svg = render_svg(chart)
    text = await interpret_natal_chart(chart, name=bd.name)
    await add_reading(
        session,
        user_id=user.telegram_id,
        reading_type="natal",
        ai_response=text,
    )

    settings = get_settings()
    kb = InlineKeyboardBuilder()
    if settings.webapp_public_url.startswith("https"):
        kb.button(
            text="🔭 Интерактивная карта",
            web_app=WebAppInfo(url=settings.mini_app_url),
        )

    await placeholder.delete()
    await message.answer_document(
        BufferedInputFile(svg.encode("utf-8"), filename="natal_chart.svg"),
        caption=(
            f"🌟 Натальная карта\n"
            f"☉ Солнце: {chart.sun_sign_ru()}\n"
            f"☽ Луна: {chart.moon_sign_ru()}\n"
            f"ASC: {chart.ascendant_sign_ru()}"
        ),
        reply_markup=kb.as_markup() if kb.export() else None,
    )
    for chunk in _split(text, 3800):
        await message.answer(chunk)


def _split(text: str, n: int):
    for i in range(0, len(text), n):
        yield text[i : i + n]
