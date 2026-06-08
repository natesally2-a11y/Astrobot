"""Shared helpers for handlers."""
from __future__ import annotations

from typing import Optional

from aiogram.types import BufferedInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.calculations import NatalChart
from app.astrology.chart_renderer import render_natal_chart_svg, svg_to_png_bytes
from app.astrology.service import build_chart_from_model
from app.bot import texts
from app.database import crud
from app.database.models import BirthData, User


async def get_birth_data_or_prompt(
    message: Message, session: AsyncSession, user: User
) -> Optional[BirthData]:
    """Return birth data or send the 'create profile first' prompt."""
    bd = await crud.get_birth_data(session, user.telegram_id)
    if bd is None:
        await message.answer(texts.NEED_PROFILE)
        return None
    return bd


def chart_from_birth_data(bd: BirthData) -> NatalChart:
    return build_chart_from_model(bd)


async def send_chart_image(message: Message, chart: NatalChart, caption: str = "") -> None:
    """Send the rendered natal chart as PNG (if possible) or SVG document."""
    svg = render_natal_chart_svg(chart)
    png = svg_to_png_bytes(svg)
    if png:
        photo = BufferedInputFile(png, filename="natal_chart.png")
        await message.answer_photo(photo, caption=caption[:1024] if caption else None)
    else:
        doc = BufferedInputFile(svg.encode("utf-8"), filename="natal_chart.svg")
        await message.answer_document(doc, caption=caption[:1024] if caption else None)
