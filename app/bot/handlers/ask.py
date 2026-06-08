from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology import AIInterpreter
from app.bot.handlers.chart import _get_chart_for_user
from app.bot.keyboards.inline import main_menu_keyboard, start_keyboard, subscription_keyboard
from app.bot.states import AskStates
from app.database import crud

router = Router()
ai = AIInterpreter()


@router.message(Command("ask"))
async def cmd_ask(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await crud.get_user(session, message.from_user.id)
    if not user or not user.birth_data:
        await message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        return

    if not await crud.can_ask_question(session, user):
        await message.answer(
            "🔒 Лимит вопросов на сегодня исчерпан (5/день).\n"
            "Оформите Pro для безлимитных вопросов.",
            reply_markup=subscription_keyboard(),
        )
        return

    await state.set_state(AskStates.waiting_question)
    await message.answer("🔮 Задайте ваш вопрос астрологу:")


@router.callback_query(F.data == "cmd_ask")
async def callback_ask(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    user = await crud.get_user(session, callback.from_user.id)
    if not user or not user.birth_data:
        await callback.message.answer("❌ Сначала создайте натальную карту.", reply_markup=start_keyboard())
        await callback.answer()
        return

    if not await crud.can_ask_question(session, user):
        await callback.message.answer(
            "🔒 Лимит вопросов исчерпан.",
            reply_markup=subscription_keyboard(),
        )
        await callback.answer()
        return

    await state.set_state(AskStates.waiting_question)
    await callback.message.answer("🔮 Задайте ваш вопрос астрологу:")
    await callback.answer()


@router.message(AskStates.waiting_question)
async def process_question(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user, chart, _ = await _get_chart_for_user(session, message.from_user.id)
    if not chart:
        await message.answer("❌ Сначала создайте натальную карту.")
        await state.clear()
        return

    if not await crud.can_ask_question(session, user):
        await message.answer("🔒 Лимит вопросов исчерпан.", reply_markup=subscription_keyboard())
        await state.clear()
        return

    question = message.text.strip()
    await message.answer("🔮 Размышляю над вашим вопросом...")
    answer = await ai.answer_question(chart, question, message.from_user.first_name or "друг")
    await crud.increment_question_count(session, user)
    await crud.save_reading(session, user.telegram_id, "ask", question, answer)
    await state.clear()
    await message.answer(f"🔮 **Ответ астролога**\n\n{answer}", parse_mode="Markdown", reply_markup=main_menu_keyboard())
