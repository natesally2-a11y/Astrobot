from __future__ import annotations

from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.astrology.ai_interpreter import interpret_compatibility
from app.astrology.calculations import calculate_natal_chart, compatibility_score
from app.bot.states import CompatibilityState
from app.bot.utils.formatters import premium_gate_text
from app.database.crud import create_reading, get_user
from app.database.models import BirthData
from app.database.session import AsyncSessionLocal
from app.services.geocoding import GeocodingService
from app.services.subscriptions import ORACLE_PLAN, PRO_PLAN, resolve_user_tier


router = Router(name="compatibility")
geocoder = GeocodingService()


def _parse_partner_payload(text: str) -> tuple[datetime.date, datetime.time, str]:
    parts = [part.strip() for part in text.split("|")]
    if len(parts) != 3:
        raise ValueError("bad-format")

    partner_date = datetime.strptime(parts[0], "%Y-%m-%d").date()
    partner_time = datetime.strptime(parts[1], "%H:%M").time()
    return partner_date, partner_time, parts[2]


@router.message(Command("compatibility"))
async def begin_compatibility(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await get_user(session, message.from_user.id)
        tier = await resolve_user_tier(session, user)

    if tier not in {PRO_PLAN.code, ORACLE_PLAN.code}:
        await message.answer(premium_gate_text())
        return

    await state.set_state(CompatibilityState.waiting_for_partner_data)
    await message.answer(
        "Отправьте данные партнера в формате:\n"
        "YYYY-MM-DD | HH:MM | Город\n\n"
        "Пример: 1993-08-14 | 18:20 | Saint Petersburg"
    )


@router.message(CompatibilityState.waiting_for_partner_data)
async def handle_partner_data(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        await message.answer("Пожалуйста, отправьте данные партнера текстом.")
        return

    try:
        partner_date, partner_time, partner_city = _parse_partner_payload(message.text)
    except ValueError:
        await message.answer(
            "Не удалось разобрать формат. Используйте: YYYY-MM-DD | HH:MM | Город"
        )
        return

    async with AsyncSessionLocal() as session:
        birth_data = await session.get(BirthData, message.from_user.id)
        if birth_data is None:
            await message.answer("Сначала создайте вашу натальную карту через /start.")
            await state.clear()
            return

    locations = await geocoder.search_city(partner_city, limit=1)
    if not locations:
        await message.answer("Не удалось найти город партнера. Попробуйте еще раз.")
        return

    partner_location = locations[0]
    user_chart = calculate_natal_chart(
        birth_date=birth_data.birth_date,
        birth_time=birth_data.birth_time,
        birth_place=birth_data.birth_place,
        latitude=birth_data.latitude,
        longitude=birth_data.longitude,
        timezone_name=birth_data.timezone,
    )
    partner_chart = calculate_natal_chart(
        birth_date=partner_date,
        birth_time=partner_time,
        birth_place=partner_location.display_name,
        latitude=partner_location.latitude,
        longitude=partner_location.longitude,
        timezone_name=partner_location.timezone,
    )
    compatibility = compatibility_score(user_chart, partner_chart)
    interpretation = await interpret_compatibility(user_chart, partner_chart, compatibility)
    text = (
        f"{compatibility['summary']}\n\n"
        f"{interpretation}"
    )
    await message.answer(text)

    async with AsyncSessionLocal() as session:
        await create_reading(
            session=session,
            telegram_id=message.from_user.id,
            reading_type="compatibility",
            question=message.text,
            ai_response=text,
            metadata_json={"score": compatibility["score"]},
        )

    await state.clear()
