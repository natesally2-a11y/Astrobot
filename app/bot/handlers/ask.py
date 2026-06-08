"""Команда /ask — задать вопрос ИИ-астрологу (с лимитом для Free)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import answer_question
from app.bot import texts
from app.bot.handlers.common import require_chart
from app.bot.states import AskFlow
from app.bot.utils import reply_long
from app.database import crud

router = Router(name="ask")


@router.message(Command("ask"))
async def cmd_ask(message: Message, state: FSMContext, session: AsyncSession) -> None:
    chart = await require_chart(message, session, message.from_user.id)
    if chart is None:
        return

    # Если вопрос передан сразу: /ask что меня ждёт в любви
    text = message.text or ""
    parts = text.split(maxsplit=1)
    if len(parts) > 1:
        await _process_question(message, session, message.from_user.id, parts[1])
        return

    await state.set_state(AskFlow.question)
    await message.answer(texts.ASK_QUESTION_PROMPT)


@router.callback_query(F.data == "menu:ask")
async def cb_ask(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await state.set_state(AskFlow.question)
    await call.message.answer(texts.ASK_QUESTION_PROMPT)


@router.message(AskFlow.question, F.text)
async def receive_question(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await state.clear()
    await _process_question(message, session, message.from_user.id, message.text.strip())


async def _process_question(
    message: Message, session: AsyncSession, user_id: int, question: str
) -> None:
    chart = await require_chart(message, session, user_id)
    if chart is None:
        return

    allowed = await crud.check_and_increment_ask(session, user_id)
    if not allowed:
        await message.answer(texts.LIMIT_REACHED)
        return

    status = await message.answer(texts.THINKING)
    answer = await answer_question(chart, question)
    await status.delete()
    await reply_long(message, f"🔮 <b>Ответ астролога</b>\n\n{answer}")
    await crud.save_reading(session, user_id, "ask", answer, question=question)
