from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from app.astrology.ai_interpreter import AstrologyInterpreter
from app.astrology.calculations import calculate_natal_chart
from app.astrology.chart_renderer import render_chart_svg
from app.bot.keyboards.inline import app_keyboard, settings_keyboard
from app.bot.states import AskAstrologer, Compatibility
from app.bot.utils.geocoding import search_cities
from app.bot.utils.parsing import parse_partner_data
from app.bot.utils.texts import HELP_TEXT, NEED_PROFILE_TEXT, PREMIUM_REQUIRED_TEXT
from app.config import get_settings
from app.database.crud import add_reading, count_daily_questions, get_user_with_birth_data, is_paid_user
from app.database.models import ReadingType
from app.database.session import async_session

router = Router(name="commands")


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("chart"))
async def chart_command(message: Message) -> None:
    chart_context = await _load_chart(message)
    if chart_context is None:
        await message.answer(NEED_PROFILE_TEXT)
        return

    chart, user_id = chart_context
    interpreter = AstrologyInterpreter()
    reading = await interpreter.natal_reading(chart)
    svg = render_chart_svg(chart)

    async with async_session() as session:
        await add_reading(session, user_id, ReadingType.NATAL.value, reading)

    await message.answer_document(
        BufferedInputFile(svg.encode("utf-8"), filename="stellarium-chart.svg"),
        caption=reading,
        reply_markup=app_keyboard(get_settings().webapp_url),
    )


@router.message(Command("today"))
async def today_command(message: Message) -> None:
    chart_context = await _load_chart(message)
    if chart_context is None:
        await message.answer(NEED_PROFILE_TEXT)
        return

    chart, user_id = chart_context
    async with async_session() as session:
        user = await get_user_with_birth_data(session, user_id)
        detailed = is_paid_user(user)

    reading = await AstrologyInterpreter().daily_forecast(chart, detailed=detailed)
    async with async_session() as session:
        await add_reading(session, user_id, ReadingType.DAILY.value, reading)
    await message.answer(reading)


@router.message(Command("week"))
async def week_command(message: Message) -> None:
    await _premium_forecast(message, ReadingType.WEEKLY.value)


@router.message(Command("transit"))
async def transit_command(message: Message) -> None:
    await _premium_forecast(message, ReadingType.TRANSIT.value)


@router.message(Command("ask"))
async def ask_command(message: Message, state: FSMContext) -> None:
    chart_context = await _load_chart(message)
    if chart_context is None:
        await message.answer(NEED_PROFILE_TEXT)
        return

    await state.set_state(AskAstrologer.waiting_for_question)
    await message.answer("Напишите вопрос астрологу. Я отвечу с учетом вашей натальной карты.")


@router.message(AskAstrologer.waiting_for_question)
async def receive_question(message: Message, state: FSMContext) -> None:
    chart_context = await _load_chart(message)
    if chart_context is None:
        await state.clear()
        await message.answer(NEED_PROFILE_TEXT)
        return

    chart, user_id = chart_context
    question = (message.text or "").strip()
    if not question:
        await message.answer("Напишите вопрос текстом.")
        return

    async with async_session() as session:
        user = await get_user_with_birth_data(session, user_id)
        if not is_paid_user(user):
            used_questions = await count_daily_questions(session, user_id)
            if used_questions >= get_settings().free_daily_questions:
                await message.answer(
                    "На бесплатном тарифе доступно 5 вопросов в день. Оформите Pro в /settings для безлимита."
                )
                return

    answer = await AstrologyInterpreter().answer_question(chart, question)
    async with async_session() as session:
        await add_reading(session, user_id, ReadingType.QUESTION.value, answer, question=question)

    await state.clear()
    await message.answer(answer)


@router.message(Command("compatibility"))
async def compatibility_command(message: Message, state: FSMContext) -> None:
    chart_context = await _load_chart(message)
    if chart_context is None:
        await message.answer(NEED_PROFILE_TEXT)
        return

    await state.set_state(Compatibility.waiting_for_partner_data)
    await message.answer(
        "Введите данные партнера одной строкой:\n"
        "ДД.ММ.ГГГГ; ЧЧ:ММ; город\n\n"
        "Например: 15.07.1990; 18:20; Казань"
    )


@router.message(Compatibility.waiting_for_partner_data)
async def receive_partner_data(message: Message, state: FSMContext) -> None:
    chart_context = await _load_chart(message)
    if chart_context is None:
        await state.clear()
        await message.answer(NEED_PROFILE_TEXT)
        return

    try:
        partner_date, partner_time, partner_city = parse_partner_data(message.text or "")
    except ValueError:
        await message.answer("Формат: ДД.ММ.ГГГГ; ЧЧ:ММ; город")
        return

    try:
        cities = await search_cities(partner_city, limit=1)
    except Exception:
        cities = []

    city = cities[0] if cities else {"place": partner_city, "latitude": None, "longitude": None}
    user_chart, user_id = chart_context
    partner_chart = calculate_natal_chart(
        partner_date,
        partner_time,
        str(city["place"]),
        float(city["latitude"]) if city.get("latitude") is not None else None,
        float(city["longitude"]) if city.get("longitude") is not None else None,
    )
    reading = await AstrologyInterpreter().compatibility(user_chart, partner_chart)

    async with async_session() as session:
        await add_reading(session, user_id, ReadingType.COMPATIBILITY.value, reading)

    await state.clear()
    await message.answer(reading)


@router.message(Command("settings"))
async def settings_command(message: Message) -> None:
    settings = get_settings()
    user_id = message.from_user.id if message.from_user else 0
    async with async_session() as session:
        user = await get_user_with_birth_data(session, user_id)

    plan = user.subscription_type if user else "free"
    expires = user.subscription_expires_at.strftime("%d.%m.%Y") if user and user.subscription_expires_at else "не задано"
    await message.answer(
        f"⚙️ Настройки Stellarium AI\n\nТекущий тариф: {plan}\nДействует до: {expires}\n\n"
        "Подписки оформляются через Telegram Stars:\n"
        "• Stellarium Pro — 50 Stars / месяц\n"
        "• Космический Оракул — 150 Stars / месяц",
        reply_markup=settings_keyboard(settings.webapp_url),
    )


async def _premium_forecast(message: Message, reading_type: str) -> None:
    chart_context = await _load_chart(message)
    if chart_context is None:
        await message.answer(NEED_PROFILE_TEXT)
        return

    chart, user_id = chart_context
    async with async_session() as session:
        user = await get_user_with_birth_data(session, user_id)
        if not is_paid_user(user):
            await message.answer(PREMIUM_REQUIRED_TEXT)
            return

    interpreter = AstrologyInterpreter()
    if reading_type == ReadingType.WEEKLY.value:
        reading = await interpreter.weekly_forecast(chart)
    else:
        reading = await interpreter.transit_forecast(chart)

    async with async_session() as session:
        await add_reading(session, user_id, reading_type, reading)
    await message.answer(reading)


async def _load_chart(message: Message):
    if message.from_user is None:
        return None

    async with async_session() as session:
        user = await get_user_with_birth_data(session, message.from_user.id)

    if user is None or user.birth_data is None or not user.gdpr_consent:
        return None

    birth = user.birth_data
    chart = calculate_natal_chart(
        birth.birth_date,
        birth.birth_time,
        birth.birth_place,
        float(birth.latitude) if birth.latitude is not None else None,
        float(birth.longitude) if birth.longitude is not None else None,
    )
    return chart, user.telegram_id


@router.message(F.text == "/app")
async def app_command(message: Message) -> None:
    settings = get_settings()
    if not settings.webapp_url:
        await message.answer("Mini App URL не настроен. Укажите WEBAPP_URL в окружении.")
        return
    await message.answer("Откройте интерактивную натальную карту:", reply_markup=app_keyboard(settings.webapp_url))
