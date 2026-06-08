"""Команда /chart — натальная карта + ИИ-анализ."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import interpret_natal
from app.astrology.chart_renderer import render_chart_svg
from app.astrology.chart_summary import chart_to_text
from app.bot import texts
from app.bot.handlers.common import require_chart
from app.bot.keyboards.common import open_app_keyboard
from app.bot.utils import reply_long
from app.database import crud

router = Router(name="chart")


async def _send_chart(message: Message, session: AsyncSession, user_id: int) -> None:
    chart = await require_chart(message, session, user_id)
    if chart is None:
        return

    user = await crud.get_user(session, user_id)
    name = user.first_name if user else None

    # SVG-карта как документ + интерактивный просмотр в Mini App
    svg = render_chart_svg(chart)
    doc = BufferedInputFile(svg.encode("utf-8"), filename="natal_chart.svg")
    await message.answer_document(
        doc,
        caption="🪐 Ваша натальная карта (SVG). Интерактивный вид — в приложении.",
        reply_markup=open_app_keyboard(),
    )

    await message.answer(f"<b>Позиции планет</b>\n<pre>{chart_to_text(chart)}</pre>")

    status = await message.answer(texts.THINKING)
    analysis = await interpret_natal(chart, name)
    await status.delete()
    await reply_long(message, "🌟 <b>Анализ натальной карты</b>\n\n" + analysis)
    await crud.save_reading(session, user_id, "natal", analysis)


@router.message(Command("chart"))
async def cmd_chart(message: Message, session: AsyncSession) -> None:
    await _send_chart(message, session, message.from_user.id)


@router.callback_query(F.data == "menu:chart")
async def cb_chart(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    await _send_chart(call.message, session, call.from_user.id)
