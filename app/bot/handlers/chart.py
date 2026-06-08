"""/chart — natal chart image + AI interpretation."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology import ai_interpreter
from app.bot import texts
from app.bot.handlers._common import (
    chart_from_birth_data,
    get_birth_data_or_prompt,
    send_chart_image,
)
from app.database import crud
from app.database.models import User

router = Router(name="chart")


@router.message(Command("chart"))
async def cmd_chart(message: Message, session: AsyncSession, user: User) -> None:
    bd = await get_birth_data_or_prompt(message, session, user)
    if bd is None:
        return

    thinking = await message.answer(texts.CALCULATING)
    chart = chart_from_birth_data(bd)

    caption_lines = ["🪐 *Ваша натальная карта*"]
    if chart.sun_sign is not None:
        from app.astrology.constants import SIGN_NAMES_RU

        caption_lines.append(f"☉ Солнце: {SIGN_NAMES_RU[chart.sun_sign]}")
    if chart.moon_sign is not None:
        from app.astrology.constants import SIGN_NAMES_RU

        caption_lines.append(f"☽ Луна: {SIGN_NAMES_RU[chart.moon_sign]}")
    if chart.ascendant_sign is not None:
        from app.astrology.constants import SIGN_NAMES_RU

        caption_lines.append(f"↑ Асцендент: {SIGN_NAMES_RU[chart.ascendant_sign]}")
    elif not bd.time_known:
        caption_lines.append("_(время рождения неизвестно — без домов и асцендента)_")

    await send_chart_image(message, chart, caption="\n".join(caption_lines))

    interpretation = await ai_interpreter.interpret_natal(chart, name=user.first_name)
    await crud.save_reading(session, user.telegram_id, "natal", interpretation)

    await thinking.delete()
    await message.answer(interpretation, parse_mode="Markdown")
