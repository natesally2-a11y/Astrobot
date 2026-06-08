"""Handler for /chart — natal chart display and AI interpretation."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from app.database.crud import get_user_with_birth_data
from app.astrology.calculations import calculate_natal_chart, format_chart_text
from app.astrology.chart_renderer import render_natal_chart_svg
from app.astrology.ai_interpreter import interpret_natal_chart

router = Router()


@router.message(Command("chart"))
async def cmd_chart(message: Message):
    if not message.from_user:
        return

    user = await get_user_with_birth_data(message.from_user.id)
    if not user or not user.birth_data:
        await message.answer(
            "❌ Сначала нужно ввести данные рождения.\n"
            "Используйте /start для начала."
        )
        return

    bd = user.birth_data
    await message.answer("🔮 Рассчитываю натальную карту...")

    chart = calculate_natal_chart(
        birth_date=bd.birth_date,
        birth_time=bd.birth_time,
        latitude=float(bd.latitude) if bd.latitude else 55.7558,
        longitude=float(bd.longitude) if bd.longitude else 37.6173,
    )

    chart_text = format_chart_text(chart)
    await message.answer(chart_text)

    svg_content = render_natal_chart_svg(chart)
    svg_bytes = svg_content.encode("utf-8")
    svg_file = BufferedInputFile(svg_bytes, filename="natal_chart.svg")
    await message.answer_document(svg_file, caption="🌟 Ваша натальная карта (SVG)")

    await message.answer("🤖 Анализирую карту с помощью ИИ...")
    interpretation = await interpret_natal_chart(chart, user_name=user.first_name or "")
    await message.answer(interpretation, parse_mode="Markdown")

    from app.database.crud import save_reading
    await save_reading(
        user_id=message.from_user.id,
        reading_type="natal",
        ai_response=interpretation,
    )
