"""Astrological reading commands: /chart, /today, /week, /ask, /transit, /compatibility."""

from __future__ import annotations

import logging
from datetime import date, time

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import (
    interpret_compatibility,
    interpret_daily,
    interpret_natal,
    interpret_question,
    interpret_transit,
    interpret_weekly,
)
from app.astrology.calculations import (
    compute_natal_chart,
    compute_transits,
    summarize_chart,
    synastry,
)
from app.astrology.chart_renderer import render_chart_svg
from app.astrology.geocoding import geocode_city
from app.bot.keyboards.inline import (
    cancel_kb,
    main_menu_kb,
    open_webapp_kb,
    subscription_kb,
)
from app.bot.utils.access import has_active_premium
from app.config import settings
from app.database import crud
from app.database.models import BirthData, User

logger = logging.getLogger(__name__)
router = Router(name="readings")


class CompatibilityFlow(StatesGroup):
    waiting_partner = State()


class AskFlow(StatesGroup):
    waiting_question = State()


async def _require_chart(message: Message, session: AsyncSession, user: User) -> BirthData | None:
    birth = await crud.get_birth_data(session, user.telegram_id)
    if birth is None:
        await message.answer(
            "Сначала создайте натальную карту: /start или нажмите кнопку ниже.",
            reply_markup=main_menu_kb(has_chart=False),
        )
        return None
    return birth


def _chart_from_birth(birth: BirthData):
    return compute_natal_chart(
        birth_date=birth.birth_date,
        birth_time=birth.birth_time,
        latitude=float(birth.latitude) if birth.latitude is not None else None,
        longitude=float(birth.longitude) if birth.longitude is not None else None,
        tz_name=birth.timezone,
    )


# ---------- /chart ----------

@router.message(Command("chart"))
async def cmd_chart(message: Message, session: AsyncSession, user: User) -> None:
    await _send_chart(message, session, user)


@router.callback_query(F.data == "menu:chart")
async def cb_chart(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await _send_chart(callback.message, session, user)
    await callback.answer()


async def _send_chart(message: Message, session: AsyncSession, user: User) -> None:
    birth = await _require_chart(message, session, user)
    if birth is None:
        return
    await message.answer("🪐 Считаю карту…")
    chart = _chart_from_birth(birth)
    svg = render_chart_svg(chart)
    file = BufferedInputFile(svg.encode("utf-8"), filename="natal_chart.svg")
    await message.answer_document(
        document=file,
        caption=(
            f"<b>Натальная карта</b>\nМесто: {birth.birth_place}\n"
            f"Дата: {birth.birth_date.strftime('%d.%m.%Y')}"
        ),
        parse_mode="HTML",
    )
    text_summary = summarize_chart(chart, lang="ru")
    await message.answer(f"<pre>{text_summary}</pre>", parse_mode="HTML")
    interpretation = await interpret_natal(chart, user.first_name)
    await crud.save_reading(
        session,
        telegram_id=user.telegram_id,
        reading_type="natal",
        question=None,
        ai_response=interpretation,
    )
    await message.answer(interpretation, reply_markup=open_webapp_kb())


# ---------- /today ----------

@router.message(Command("today"))
async def cmd_today(message: Message, session: AsyncSession, user: User) -> None:
    await _send_today(message, session, user)


@router.callback_query(F.data == "menu:today")
async def cb_today(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await _send_today(callback.message, session, user)
    await callback.answer()


async def _send_today(message: Message, session: AsyncSession, user: User) -> None:
    birth = await _require_chart(message, session, user)
    if birth is None:
        return
    asked = await crud.count_questions_today(session, user.telegram_id)
    if not has_active_premium(user) and asked >= settings.free_daily_questions:
        await message.answer(
            "Бесплатный лимит на сегодня исчерпан.\n"
            "Обновите подписку для безлимитных прогнозов:",
            reply_markup=subscription_kb(),
        )
        return
    await message.answer("🌞 Считаю транзиты на сегодня…")
    chart = _chart_from_birth(birth)
    transits = compute_transits(chart)
    text = await interpret_daily(chart, transits, user.first_name)
    await crud.save_reading(
        session,
        telegram_id=user.telegram_id,
        reading_type="daily",
        question=None,
        ai_response=text,
    )
    await message.answer(text)


# ---------- /week ----------

@router.message(Command("week"))
async def cmd_week(message: Message, session: AsyncSession, user: User) -> None:
    await _send_week(message, session, user)


@router.callback_query(F.data == "menu:week")
async def cb_week(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await _send_week(callback.message, session, user)
    await callback.answer()


async def _send_week(message: Message, session: AsyncSession, user: User) -> None:
    if not has_active_premium(user):
        await message.answer(
            "Прогноз на неделю доступен в Stellarium Pro / Oracle.",
            reply_markup=subscription_kb(),
        )
        return
    birth = await _require_chart(message, session, user)
    if birth is None:
        return
    await message.answer("🌙 Готовлю прогноз на неделю…")
    chart = _chart_from_birth(birth)
    transits = compute_transits(chart)
    text = await interpret_weekly(chart, transits, user.first_name)
    await crud.save_reading(
        session,
        telegram_id=user.telegram_id,
        reading_type="weekly",
        question=None,
        ai_response=text,
    )
    await message.answer(text)


# ---------- /transit ----------

@router.message(Command("transit"))
async def cmd_transit(message: Message, session: AsyncSession, user: User) -> None:
    await _send_transits(message, session, user)


@router.callback_query(F.data == "menu:transit")
async def cb_transit(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await _send_transits(callback.message, session, user)
    await callback.answer()


async def _send_transits(message: Message, session: AsyncSession, user: User) -> None:
    if not has_active_premium(user):
        await message.answer(
            "Расширенный анализ транзитов доступен в Pro / Oracle.",
            reply_markup=subscription_kb(),
        )
        return
    birth = await _require_chart(message, session, user)
    if birth is None:
        return
    chart = _chart_from_birth(birth)
    transits = compute_transits(chart)
    text = await interpret_transit(transits)
    await crud.save_reading(
        session,
        telegram_id=user.telegram_id,
        reading_type="transit",
        question=None,
        ai_response=text,
    )
    await message.answer(text)


# ---------- /ask ----------

@router.message(Command("ask"))
async def cmd_ask(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    birth = await _require_chart(message, session, user)
    if birth is None:
        return
    question = (command.args or "").strip()
    if not question:
        await state.set_state(AskFlow.waiting_question)
        await message.answer(
            "Задайте свой вопрос астрологу одним сообщением:",
            reply_markup=cancel_kb(),
        )
        return
    await _answer_question(message, session, user, birth, question)


@router.callback_query(F.data == "menu:ask")
async def cb_ask(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AskFlow.waiting_question)
    await callback.message.answer(
        "Задайте свой вопрос астрологу одним сообщением:",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(AskFlow.waiting_question)
async def ask_question(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    question = (message.text or "").strip()
    if len(question) < 3:
        await message.answer("Опишите вопрос подробнее (минимум 3 символа).")
        return
    birth = await _require_chart(message, session, user)
    if birth is None:
        await state.clear()
        return
    await state.clear()
    await _answer_question(message, session, user, birth, question)


async def _answer_question(
    message: Message,
    session: AsyncSession,
    user: User,
    birth: BirthData,
    question: str,
) -> None:
    asked = await crud.count_questions_today(session, user.telegram_id)
    if not has_active_premium(user) and asked >= settings.free_daily_questions:
        await message.answer(
            "Бесплатный лимит вопросов на сегодня исчерпан 🌙\n"
            "Обновите подписку, чтобы продолжить.",
            reply_markup=subscription_kb(),
        )
        return
    await message.answer("✨ Размышляю…")
    chart = _chart_from_birth(birth)
    transits = compute_transits(chart)
    text = await interpret_question(chart, transits, question, user.first_name)
    await crud.save_reading(
        session,
        telegram_id=user.telegram_id,
        reading_type="ask",
        question=question,
        ai_response=text,
    )
    await message.answer(text)


# ---------- /compatibility ----------

@router.message(Command("compatibility"))
async def cmd_compatibility(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    birth = await _require_chart(message, session, user)
    if birth is None:
        return
    await state.set_state(CompatibilityFlow.waiting_partner)
    await message.answer(
        "💞 <b>Совместимость</b>\n\n"
        "Пришлите данные партнёра одной строкой в формате:\n"
        "<code>YYYY-MM-DD HH:MM Город</code>\n"
        "Например: <code>1990-04-12 14:30 Санкт-Петербург</code>\n\n"
        "Если время неизвестно — пропустите его: <code>1990-04-12 - Санкт-Петербург</code>",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:compat")
async def cb_compatibility(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    await cmd_compatibility(callback.message, state, session, user)
    await callback.answer()


@router.message(CompatibilityFlow.waiting_partner)
async def compatibility_partner(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    raw = (message.text or "").strip()
    parts = raw.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "Не могу разобрать. Формат: YYYY-MM-DD HH:MM Город (HH:MM можно"
            " заменить на '-')."
        )
        return
    date_part, time_part, place = parts
    try:
        partner_date = date.fromisoformat(date_part)
    except ValueError:
        await message.answer("Неверная дата. Используйте формат YYYY-MM-DD.")
        return
    partner_time: time | None
    if time_part == "-":
        partner_time = None
    else:
        try:
            partner_time = time.fromisoformat(time_part)
        except ValueError:
            await message.answer("Неверное время. Используйте HH:MM или '-'.")
            return

    await message.answer("🔎 Ищу город партнёра…")
    geo = await geocode_city(place)
    if geo is None:
        await message.answer("Не нашёл такой город, попробуйте другой формат.")
        return

    birth = await _require_chart(message, session, user)
    if birth is None:
        await state.clear()
        return

    chart_user = _chart_from_birth(birth)
    chart_partner = compute_natal_chart(
        birth_date=partner_date,
        birth_time=partner_time,
        latitude=geo.latitude,
        longitude=geo.longitude,
        tz_name=geo.timezone,
    )
    cross = synastry(chart_user, chart_partner)
    text = await interpret_compatibility(
        chart_user, chart_partner, cross, user.first_name, "Партнёр"
    )
    await crud.save_reading(
        session,
        telegram_id=user.telegram_id,
        reading_type="compatibility",
        question=f"{partner_date} {partner_time} {geo.display_name}",
        ai_response=text,
    )
    await state.clear()
    await message.answer(text)
