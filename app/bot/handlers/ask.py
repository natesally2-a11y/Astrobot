"""Handler for /ask — freeform questions to the AI astrologer."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.crud import (
    get_user_with_birth_data,
    check_subscription_level,
    check_daily_limit,
    increment_daily_questions,
    save_reading,
)
from app.astrology.calculations import calculate_natal_chart
from app.astrology.ai_interpreter import ask_astrologer
from app.bot.keyboards.inline import subscription_keyboard
from app.config import settings

router = Router()


@router.message(Command("ask"))
async def cmd_ask(message: Message):
    if not message.from_user:
        return

    args = message.text.split(maxsplit=1) if message.text else []
    if len(args) < 2:
        await message.answer(
            "❓ <b>Задайте вопрос астрологу</b>\n\n"
            "Формат: <code>/ask ваш вопрос</code>\n\n"
            "Примеры:\n"
            "• /ask Что меня ждёт в любви?\n"
            "• /ask Стоит ли менять работу?\n"
            "• /ask Какие мои сильные стороны?",
            parse_mode="HTML",
        )
        return

    question = args[1]

    level = await check_subscription_level(message.from_user.id)
    if level == "free":
        can_ask, remaining = await check_daily_limit(
            message.from_user.id, settings.free_daily_questions
        )
        if not can_ask:
            await message.answer(
                "⚠️ Лимит бесплатных вопросов на сегодня исчерпан.\n"
                "Оформите подписку для безлимита:",
                reply_markup=subscription_keyboard(),
            )
            return

    user = await get_user_with_birth_data(message.from_user.id)
    chart = None
    user_name = ""
    if user:
        user_name = user.first_name or ""
        if user.birth_data:
            bd = user.birth_data
            chart = calculate_natal_chart(
                birth_date=bd.birth_date,
                birth_time=bd.birth_time,
                latitude=float(bd.latitude) if bd.latitude else 55.7558,
                longitude=float(bd.longitude) if bd.longitude else 37.6173,
            )

    await message.answer("🔮 Консультируюсь со звёздами...")
    answer = await ask_astrologer(question, chart=chart, user_name=user_name)
    await message.answer(answer, parse_mode="Markdown")

    if level == "free":
        await increment_daily_questions(message.from_user.id)
        _, remaining = await check_daily_limit(
            message.from_user.id, settings.free_daily_questions
        )
        await message.answer(
            f"ℹ️ Осталось бесплатных вопросов: {remaining}/{settings.free_daily_questions}"
        )

    await save_reading(
        user_id=message.from_user.id,
        reading_type="ask",
        question=question,
        ai_response=answer,
    )
