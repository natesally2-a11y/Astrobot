from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from app.astrology.ai_interpreter import AstrologyAIInterpreter
from app.astrology.calculations import (
    NatalChart,
    build_natal_chart,
    compatibility_snapshot,
    daily_transit_summary,
)
from app.astrology.chart_renderer import render_chart_svg
from app.bot.keyboards.subscription import settings_keyboard
from app.bot.middlewares.subscription import is_premium
from app.bot.texts import DISCLAIMER_TEXT, HELP_TEXT
from app.config import get_settings
from app.database.crud import (
    count_daily_questions,
    create_reading,
    delete_user_data,
    get_readings,
    get_user_with_birth_data,
)
from app.database.session import AsyncSessionLocal

router = Router(name="commands")
settings = get_settings()
ai_interpreter = AstrologyAIInterpreter()


def _chart_from_birth_data(birth_data) -> NatalChart:
    return build_natal_chart(
        birth_date=birth_data.birth_date,
        birth_time=birth_data.birth_time,
        latitude=birth_data.latitude,
        longitude=birth_data.longitude,
    )


async def _require_profile(message: Message):
    async with AsyncSessionLocal() as session:
        user, birth_data = await get_user_with_birth_data(session, message.from_user.id)
    if not user or not birth_data:
        await message.answer("Сначала создайте карту через /start")
        return None, None
    return user, birth_data


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("chart"))
async def cmd_chart(message: Message) -> None:
    user, birth_data = await _require_profile(message)
    if not user:
        return

    chart = _chart_from_birth_data(birth_data)
    analysis = await ai_interpreter.interpret_natal(chart)
    svg = render_chart_svg(chart)
    file = BufferedInputFile(svg.encode("utf-8"), filename="natal_chart.svg")

    async with AsyncSessionLocal() as session:
        await create_reading(session, user.telegram_id, "natal", analysis)

    await message.answer_document(file, caption=analysis[:1024])


@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    user, birth_data = await _require_profile(message)
    if not user:
        return

    chart = _chart_from_birth_data(birth_data)
    transit = daily_transit_summary(chart, date.today())
    forecast = await ai_interpreter.forecast_today(chart, transit, date.today())

    async with AsyncSessionLocal() as session:
        await create_reading(session, user.telegram_id, "daily", forecast, metadata_json={"transit": transit})

    await message.answer(f"{forecast}\n\n{DISCLAIMER_TEXT}")


@router.message(Command("week"))
async def cmd_week(message: Message) -> None:
    user, birth_data = await _require_profile(message)
    if not user:
        return
    if not is_premium(user.subscription_type, user.subscription_expires_at):
        await message.answer("Команда /week доступна в Stellarium Pro и Космический Оракул. Используйте /settings.")
        return

    chart = _chart_from_birth_data(birth_data)
    summaries = []
    for i in range(7):
        day = date.today() + timedelta(days=i)
        summaries.append(f"{day.strftime('%d.%m')}: {daily_transit_summary(chart, day)}")

    response = "Прогноз на неделю:\n\n" + "\n".join(summaries)
    async with AsyncSessionLocal() as session:
        await create_reading(session, user.telegram_id, "weekly", response)
    await message.answer(response)


@router.message(Command("transit"))
async def cmd_transit(message: Message) -> None:
    user, birth_data = await _require_profile(message)
    if not user:
        return
    if not is_premium(user.subscription_type, user.subscription_expires_at):
        await message.answer("Команда /transit доступна только Premium-подписчикам.")
        return

    chart = _chart_from_birth_data(birth_data)
    transit = daily_transit_summary(chart, date.today())
    async with AsyncSessionLocal() as session:
        await create_reading(session, user.telegram_id, "transit", transit)
    await message.answer(f"Ключевой транзит дня: {transit}")


@router.message(Command("compatibility"))
async def cmd_compatibility(message: Message) -> None:
    user, birth_data = await _require_profile(message)
    if not user:
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Пример: /compatibility 1994-05-06")
        return

    try:
        partner_date = date.fromisoformat(args[1].strip())
    except ValueError:
        await message.answer("Формат даты партнера: YYYY-MM-DD. Пример: /compatibility 1994-05-06")
        return
    partner_chart = build_natal_chart(partner_date, None, None, None)
    own_chart = _chart_from_birth_data(birth_data)
    base = compatibility_snapshot(own_chart, partner_chart)
    answer = await ai_interpreter.compatibility(own_chart, partner_chart, base)

    async with AsyncSessionLocal() as session:
        await create_reading(
            session=session,
            user_id=user.telegram_id,
            reading_type="compatibility",
            ai_response=answer,
            question=args[1].strip(),
            metadata_json={"base_snapshot": base},
        )
    await message.answer(answer)


@router.message(Command("ask"))
async def cmd_ask(message: Message) -> None:
    user, birth_data = await _require_profile(message)
    if not user:
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /ask ваш вопрос")
        return

    question = args[1].strip()
    if not is_premium(user.subscription_type, user.subscription_expires_at):
        async with AsyncSessionLocal() as session:
            used = await count_daily_questions(session, user.telegram_id, date.today())
        if used >= settings.free_daily_question_limit:
            await message.answer("Лимит бесплатных вопросов на сегодня исчерпан. Попробуйте /settings для апгрейда.")
            return

    chart = _chart_from_birth_data(birth_data)
    answer = await ai_interpreter.answer_question(chart, question)
    async with AsyncSessionLocal() as session:
        await create_reading(session, user.telegram_id, "ask", answer, question=question)
    await message.answer(answer)


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    await message.answer(
        "Тарифы:\n"
        f"• Stellarium Pro — {settings.pro_monthly_stars} Stars / мес\n"
        f"• Космический Оракул — {settings.oracle_monthly_stars} Stars / мес",
        reply_markup=settings_keyboard(settings.webapp_url),
    )


@router.message(Command("privacy"))
async def cmd_privacy(message: Message) -> None:
    await message.answer(
        "Полная политика конфиденциальности доступна в файле privacy_policy.md. "
        "Данные можно выгрузить через /export_data или удалить через /delete_data."
    )


@router.message(Command("my_data"))
async def cmd_my_data(message: Message) -> None:
    user, birth_data = await _require_profile(message)
    if not user:
        return
    payload = {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "username": user.username,
        "subscription_type": user.subscription_type,
        "subscription_expires_at": str(user.subscription_expires_at) if user.subscription_expires_at else None,
        "gdpr_consent": user.gdpr_consent,
        "gdpr_consent_date": str(user.gdpr_consent_date) if user.gdpr_consent_date else None,
        "birth_data": {
            "birth_date": str(birth_data.birth_date),
            "birth_time": str(birth_data.birth_time) if birth_data.birth_time else None,
            "birth_place": birth_data.birth_place,
            "latitude": birth_data.latitude,
            "longitude": birth_data.longitude,
            "timezone": birth_data.timezone,
        },
    }
    await message.answer(f"Ваши данные:\n<pre>{json.dumps(payload, ensure_ascii=False, indent=2)}</pre>")


@router.message(Command("delete_data"))
async def cmd_delete_data(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        await delete_user_data(session, message.from_user.id)
    await message.answer("Ваши данные полностью удалены (GDPR Right to be forgotten).")


@router.message(Command("export_data"))
async def cmd_export_data(message: Message) -> None:
    user, birth_data = await _require_profile(message)
    if not user:
        return
    async with AsyncSessionLocal() as session:
        readings = await get_readings(session, user.telegram_id, limit=100)

    payload = {
        "exported_at": datetime.utcnow().isoformat(),
        "user": {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "subscription_type": user.subscription_type,
        },
        "birth_data": {
            "birth_date": str(birth_data.birth_date),
            "birth_time": str(birth_data.birth_time) if birth_data.birth_time else None,
            "birth_place": birth_data.birth_place,
            "latitude": birth_data.latitude,
            "longitude": birth_data.longitude,
            "timezone": birth_data.timezone,
        },
        "readings": [
            {
                "reading_type": r.reading_type,
                "question": r.question,
                "ai_response": r.ai_response,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in readings
        ],
    }
    file = BufferedInputFile(
        json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        filename="stellarium_export.json",
    )
    await message.answer_document(file, caption="Экспорт данных готов.")

