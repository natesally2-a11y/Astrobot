"""/ask command + free-form chat with the AI astrologer (quota-limited)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology import ai_interpreter
from app.bot import texts
from app.bot.handlers._common import chart_from_birth_data, get_birth_data_or_prompt
from app.bot.keyboards.inline import subscription_keyboard
from app.bot.states import AskFlow
from app.bot.utils import has_premium
from app.config import settings
from app.database import crud
from app.database.models import User

router = Router(name="ask")


@router.message(Command("ask"))
async def cmd_ask(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    if command.args:
        await _answer_question(message, session, user, command.args.strip())
        return
    await state.set_state(AskFlow.waiting_question)
    await message.answer(texts.ASK_PROMPT)


@router.message(AskFlow.waiting_question, F.text)
async def on_question(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    await state.clear()
    await _answer_question(message, session, user, message.text.strip())


@router.message(F.text & ~F.text.startswith("/"))
async def free_chat(message: Message, session: AsyncSession, user: User) -> None:
    """Catch-all: treat any non-command text as a question to the astrologer."""
    await _answer_question(message, session, user, message.text.strip())


async def _answer_question(
    message: Message, session: AsyncSession, user: User, question: str
) -> None:
    bd = await get_birth_data_or_prompt(message, session, user)
    if bd is None:
        return

    allowed = await crud.check_and_increment_quota(session, user, settings.free_daily_questions)
    if not allowed:
        await message.answer(
            texts.FREE_LIMIT_REACHED.format(limit=settings.free_daily_questions),
            parse_mode="Markdown",
            reply_markup=subscription_keyboard(),
        )
        return

    thinking = await message.answer(texts.CALCULATING)
    chart = chart_from_birth_data(bd)
    answer = await ai_interpreter.answer_question(chart, question, name=user.first_name)
    await crud.save_reading(session, user.telegram_id, "ask", answer, question=question)
    await thinking.delete()

    suffix = ""
    if not has_premium(user):
        left = await crud.remaining_questions(user, settings.free_daily_questions)
        suffix = f"\n\n_Осталось вопросов сегодня: {left}_"
    await message.answer(answer + suffix, parse_mode="Markdown")
