"""
/ask command handler — AI astrologer Q&A.
"""
from __future__ import annotations

from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database import crud
from app.database.models import User
from app.astrology.calculations import NatalChart
from app.astrology.ai_interpreter import answer_question
from app.bot.keyboards.inline import get_main_menu_keyboard
from app.bot.states import AskStates
from app.config import settings

router = Router(name="ask")


@router.message(Command("ask"))
async def cmd_ask(message: Message, state: FSMContext, session=None, db_user: Optional[User] = None):
    await start_ask(message, state, session, db_user)


async def start_ask(
    message: Message,
    state: FSMContext,
    session=None,
    db_user: Optional[User] = None,
):
    user_id = message.chat.id
    user = db_user or (await crud.get_user(session, user_id) if session else None)
    is_pro = user.is_pro if user else False

    if not is_pro:
        user = await crud.check_and_reset_questions(session, user)
        remaining = settings.FREE_QUESTIONS_PER_DAY - (user.questions_today or 0)
        if remaining <= 0:
            await message.answer(
                "❌ <b>Лимит вопросов исчерпан</b>\n\n"
                f"Бесплатно доступно {settings.FREE_QUESTIONS_PER_DAY} вопросов в день.\n\n"
                "⭐ Оформите Stellarium Pro для безлимитных вопросов!",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(has_birth_data=True, is_pro=False),
            )
            return
        limit_text = f"\n<i>Осталось вопросов сегодня: {remaining - 1}</i>"
    else:
        limit_text = ""

    await state.set_state(AskStates.waiting_for_question)
    await state.update_data(user_id=user_id)
    await message.answer(
        f"🔮 <b>Задайте вопрос астрологу</b>{limit_text}\n\n"
        "Введите ваш вопрос — я проанализирую его через призму вашей натальной карты:\n\n"
        "<i>Примеры:\n"
        "• Когда лучше менять работу?\n"
        "• Как улучшить отношения?\n"
        "• Что мешает моему финансовому росту?</i>",
        parse_mode="HTML",
    )


@router.message(AskStates.waiting_for_question)
async def process_question(
    message: Message, state: FSMContext, session=None, db_user: Optional[User] = None
):
    question = message.text.strip()
    if len(question) < 5:
        await message.answer("❓ Пожалуйста, задайте более развёрнутый вопрос.")
        return

    user = db_user or await crud.get_user(session, message.from_user.id)
    is_pro = user.is_pro if user else False
    user_name = user.display_name if user else "Пользователь"

    if not is_pro and session:
        user = await crud.check_and_reset_questions(session, user)
        if user.questions_today >= settings.FREE_QUESTIONS_PER_DAY:
            await message.answer(
                "❌ Лимит вопросов на сегодня исчерпан.\n"
                "Оформите Pro для безлимитных вопросов!"
            )
            await state.clear()
            return

    birth_data = await crud.get_birth_data(session, message.from_user.id)
    if not birth_data:
        await message.answer("❌ Данные рождения не найдены. Используйте /start.")
        await state.clear()
        return

    await state.clear()
    msg = await message.answer("🔮 Консультируюсь со звёздами...")

    try:
        chart = NatalChart(
            birth_date=birth_data.birth_date,
            birth_time=birth_data.birth_time,
            latitude=float(birth_data.latitude or 55.75),
            longitude=float(birth_data.longitude or 37.62),
            timezone=birth_data.timezone or "Europe/Moscow",
        )

        response = await answer_question(chart, user_name, question, is_pro)

        if not is_pro and session:
            await crud.increment_questions(session, message.from_user.id)

        await crud.save_reading(session, message.from_user.id, "question", question, response)

        await msg.delete()
        await message.answer(
            f"🔮 <b>Ответ астролога</b>\n\n"
            f"❓ <i>{question}</i>\n\n"
            f"{response}",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(has_birth_data=True, is_pro=is_pro),
        )
    except Exception:
        await msg.delete()
        await message.answer("❌ Ошибка при получении ответа. Попробуйте позже.")
