from __future__ import annotations

from datetime import date, datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import (
    answer_astrology_question,
    compatibility_interpretation,
    daily_interpretation,
    natal_interpretation,
)
from app.astrology.calculations import calculate_daily_transits, calculate_natal_chart, compatibility_score
from app.astrology.chart_renderer import render_natal_chart_svg
from app.astrology.geocoding import search_places
from app.database import crud

router = Router(name=__name__)


async def _load_ready_profile(session: AsyncSession, user_id: int):
    user, birth = await crud.get_user_full_profile(session, user_id)
    if user is None or birth is None:
        return None, None, "Сначала завершите регистрацию командой /start."
    if not user.gdpr_consent:
        return None, None, "Для работы нужен GDPR consent. Запустите /start."
    return user, birth, None


async def _build_chart(session: AsyncSession, user_id: int):
    user, birth, error = await _load_ready_profile(session, user_id)
    if error:
        return None, None, error
    chart = calculate_natal_chart(
        birth_date=birth.birth_date,
        birth_time=birth.birth_time,
        latitude=birth.latitude,
        longitude=birth.longitude,
        place=birth.birth_place,
    )
    return user, chart, None


@router.message(Command("chart"))
async def chart_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user, chart, error = await _build_chart(session, message.from_user.id)
    if error:
        await message.answer(error)
        return

    analysis = await natal_interpretation(chart, user.first_name if user else None)
    await crud.add_reading(session, message.from_user.id, "natal", analysis)

    svg = render_natal_chart_svg(chart)
    await message.answer_document(
        BufferedInputFile(svg.encode("utf-8"), filename="natal_chart.svg"),
        caption="🪐 Ваша натальная карта",
    )
    await message.answer(analysis)


@router.message(Command("today"))
async def today_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    _, chart, error = await _build_chart(session, message.from_user.id)
    if error:
        await message.answer(error)
        return
    transits = calculate_daily_transits(chart, date.today(), latitude=None, longitude=None)
    analysis = await daily_interpretation(chart, transits, date.today())
    await crud.add_reading(session, message.from_user.id, "daily", analysis)
    await message.answer(analysis)


def _is_premium(user) -> bool:
    return user.subscription_type in {"pro", "oracle"} and bool(
        user.subscription_expires_at and user.subscription_expires_at > datetime.utcnow()
    )


@router.message(Command("week"))
async def week_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user, chart, error = await _build_chart(session, message.from_user.id)
    if error:
        await message.answer(error)
        return
    if not _is_premium(user):
        await message.answer("Команда /week доступна только в Stellarium Pro и выше. Откройте /settings.")
        return
    forecasts = []
    for i in range(7):
        day = date.today() + timedelta(days=i)
        transits = calculate_daily_transits(chart, day, latitude=None, longitude=None)
        text = await daily_interpretation(chart, transits[:8], day)
        forecasts.append(f"<b>{day.isoformat()}</b>\n{text}")
    joined = "\n\n".join(forecasts[:3]) + "\n\n... (полная неделя в Mini App /app)"
    await crud.add_reading(session, message.from_user.id, "weekly", joined)
    await message.answer(joined)


@router.message(Command("transit"))
async def transit_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user, chart, error = await _build_chart(session, message.from_user.id)
    if error:
        await message.answer(error)
        return
    if not _is_premium(user):
        await message.answer("Транзиты доступны в премиум-планах. Откройте /settings.")
        return
    transits = calculate_daily_transits(chart, date.today(), latitude=None, longitude=None)
    if not transits:
        await message.answer("Сегодня мягкий фон: выраженных транзитов не найдено.")
        return
    lines = [
        f"• {t.planet_a} — {t.aspect_type} — {t.planet_b} (orb {t.orb}°)" for t in transits[:12]
    ]
    await message.answer("🌠 Ключевые транзиты дня:\n" + "\n".join(lines))


@router.message(Command("compatibility"))
async def compatibility_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    _, user_chart, error = await _build_chart(session, message.from_user.id)
    if error:
        await message.answer(error)
        return

    args = (message.text or "").split(maxsplit=3)
    if len(args) < 4:
        await message.answer(
            "Формат:\n/compatibility DD.MM.YYYY HH:MM Город\n"
            "Пример: /compatibility 15.08.1991 09:40 Berlin"
        )
        return
    try:
        partner_date = datetime.strptime(args[1], "%d.%m.%Y").date()
        partner_time = datetime.strptime(args[2], "%H:%M").time()
    except ValueError:
        await message.answer("Не удалось разобрать дату/время. Используйте DD.MM.YYYY HH:MM.")
        return
    places = await search_places(args[3], limit=1)
    if not places:
        await message.answer("Не удалось найти город партнёра.")
        return
    partner_place = places[0]
    partner_chart = calculate_natal_chart(
        birth_date=partner_date,
        birth_time=partner_time,
        latitude=partner_place["lat"],
        longitude=partner_place["lon"],
        place=partner_place["display_name"],
    )
    score, highlights = compatibility_score(user_chart, partner_chart)
    report = await compatibility_interpretation(user_chart, partner_chart, score, highlights)
    answer = f"💞 Совместимость: <b>{score}/99</b>\n\n{report}"
    await crud.add_reading(session, message.from_user.id, "compatibility", answer, question=message.text)
    await message.answer(answer)


@router.message(Command("ask"))
async def ask_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    _, chart, error = await _build_chart(session, message.from_user.id)
    if error:
        await message.answer(error)
        return
    can_ask, remaining = await crud.can_ask_question(session, message.from_user.id)
    if not can_ask:
        await message.answer(
            f"Лимит вопросов на сегодня исчерпан ({remaining} осталось). "
            "Для безлимита подключите Pro в /settings."
        )
        return

    question = (message.text or "").replace("/ask", "", 1).strip()
    if not question:
        await message.answer("Введите вопрос после команды. Пример: /ask Подходит ли неделя для переговоров?")
        return

    response = await answer_astrology_question(chart, question)
    await crud.consume_question(session, message.from_user.id)
    await crud.add_reading(session, message.from_user.id, "ask", response, question=question)
    await message.answer(response)
