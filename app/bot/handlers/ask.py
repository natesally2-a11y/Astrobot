"""Free-form Q&A with the AI astrologer (/ask)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import answer_question
from app.astrology.calculations import compute_chart
from app.bot import texts
from app.bot.states import AskFlow
from app.bot.utils.access import (
    ensure_birth_data,
    ensure_consent,
    spend_free_question,
)
from app.database.crud import add_reading, get_birth_data
from app.database.models import User

router = Router(name="ask")


@router.message(Command("ask"))
async def cmd_ask(
    message: Message, session: AsyncSession, user: User, state: FSMContext
) -> None:
    if not await ensure_consent(user, message):
        return
    if await ensure_birth_data(user, session, message) is None:
        return
    # The question itself will spend the quota; here we just initiate.
    await message.answer(texts.ASK_FOR_QUESTION)
    await state.set_state(AskFlow.waiting_question)


@router.message(StateFilter(AskFlow.waiting_question), F.text)
async def take_question(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    question = message.text.strip()
    if not question:
        return
    if not await spend_free_question(user, message):
        await state.clear()
        return

    bd = await get_birth_data(session, user.telegram_id)
    if bd is None:
        await message.answer(texts.NEED_BIRTH_DATA)
        await state.clear()
        return

    placeholder = await message.answer("✨ Думаю над вашим вопросом…")
    chart = compute_chart(
        birth_date=bd.birth_date,
        birth_time=None if bd.time_is_unknown else bd.birth_time,
        latitude=float(bd.latitude),
        longitude=float(bd.longitude),
        timezone_name=bd.timezone,
    )
    text = await answer_question(chart, question)
    await add_reading(
        session,
        user_id=user.telegram_id,
        reading_type="qa",
        question=question,
        ai_response=text,
    )
    await placeholder.delete()
    for chunk in _split(text, 3800):
        await message.answer(chunk)
    await state.clear()


def _split(text: str, n: int):
    for i in range(0, len(text), n):
        yield text[i : i + n]
