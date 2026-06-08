from datetime import date, time

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from app.astrology.ai_interpreter import (
    generate_compatibility_reading,
    generate_daily_reading,
    generate_natal_reading,
    generate_question_reading,
    generate_weekly_reading,
)
from app.astrology.calculations import BirthInfo, calculate_compatibility, calculate_daily_transits, calculate_natal_chart
from app.astrology.chart_renderer import render_chart_svg
from app.bot.states import InteractionStates
from app.config import settings
from app.database.crud import create_reading, get_questions_today, get_user, is_premium
from app.database.session import async_session_factory
from app.services.geocoding import search_places

router = Router(name='readings')


def _birth_info_from_user(user) -> BirthInfo | None:
    if user is None or user.birth_data is None:
        return None
    birth = user.birth_data
    return BirthInfo(
        birth_date=birth.birth_date,
        birth_time=birth.birth_time,
        latitude=float(birth.latitude),
        longitude=float(birth.longitude),
        timezone=birth.timezone or 'UTC',
        birth_place=birth.birth_place,
        is_time_approximate=birth.is_time_approximate,
    )


@router.message(Command('chart'))
async def chart_command(message: Message) -> None:
    async with async_session_factory() as session:
        user = await get_user(session, message.from_user.id)
        birth_info = _birth_info_from_user(user)
        if birth_info is None:
            await message.answer('Сначала заполните данные рождения через /start.')
            return
        chart = calculate_natal_chart(birth_info)
        reading = await generate_natal_reading(chart, user.first_name)
        await create_reading(session, message.from_user.id, 'natal', reading)
    svg = render_chart_svg(chart).encode('utf-8')
    await message.answer_document(BufferedInputFile(svg, filename='natal_chart.svg'))
    await message.answer(reading)


@router.message(Command('today'))
async def today_command(message: Message) -> None:
    async with async_session_factory() as session:
        user = await get_user(session, message.from_user.id)
        birth_info = _birth_info_from_user(user)
        if birth_info is None:
            await message.answer('Сначала заполните данные рождения через /start.')
            return
        chart = calculate_natal_chart(birth_info)
        transits = calculate_daily_transits(chart)
        reading = await generate_daily_reading(chart, transits, user.first_name)
        await create_reading(session, message.from_user.id, 'daily', reading)
    await message.answer(reading)


@router.message(Command('week'))
async def week_command(message: Message) -> None:
    async with async_session_factory() as session:
        premium = await is_premium(session, message.from_user.id)
        if not premium:
            await message.answer('Недельный прогноз доступен в Stellarium Pro и Cosmic Oracle. Откройте /settings для апгрейда.')
            return
        user = await get_user(session, message.from_user.id)
        birth_info = _birth_info_from_user(user)
        if birth_info is None:
            await message.answer('Сначала заполните данные рождения через /start.')
            return
        chart = calculate_natal_chart(birth_info)
        transits = calculate_daily_transits(chart)
        reading = await generate_weekly_reading(chart, transits, user.first_name)
        await create_reading(session, message.from_user.id, 'weekly', reading)
    await message.answer(reading)


@router.message(Command('transit'))
async def transit_command(message: Message) -> None:
    async with async_session_factory() as session:
        premium = await is_premium(session, message.from_user.id)
        if not premium:
            await message.answer('Подробные транзиты доступны только на платных тарифах. Откройте /settings.')
            return
        user = await get_user(session, message.from_user.id)
        birth_info = _birth_info_from_user(user)
        if birth_info is None:
            await message.answer('Сначала заполните данные рождения через /start.')
            return
        chart = calculate_natal_chart(birth_info)
        transits = calculate_daily_transits(chart)
        points = transits['important_transits']
    if not points:
        await message.answer('Сегодня нет жестких транзитных акцентов — отличный день для спокойной рутины и планирования.')
        return
    text = ['<b>Важные транзиты</b>']
    for item in points:
        text.append(f"• {item['transit_planet']} — {item['aspect']} к натальному {item['target']} (orb {item['orb']})")
    await message.answer('\n'.join(text))


@router.message(Command('ask'))
async def ask_command(message: Message, state: FSMContext) -> None:
    async with async_session_factory() as session:
        user = await get_user(session, message.from_user.id)
        if user is None or user.birth_data is None:
            await message.answer('Чтобы вопрос был персональным, сначала заполните данные рождения через /start.')
            return
        premium = await is_premium(session, message.from_user.id)
        if not premium:
            asked_today = await get_questions_today(session, message.from_user.id)
            remaining = settings.free_daily_questions - asked_today
            if remaining <= 0:
                await message.answer('Лимит бесплатных вопросов на сегодня исчерпан. Апгрейд доступен в /settings.')
                return
            await message.answer(f'У вас осталось {remaining} бесплатных вопросов на сегодня. Отправьте свой вопрос одним сообщением.')
        else:
            await message.answer('Отправьте свой вопрос одним сообщением. На платном тарифе лимит не ограничен.')
    await state.set_state(InteractionStates.waiting_for_question)


@router.message(InteractionStates.waiting_for_question)
async def receive_question(message: Message, state: FSMContext) -> None:
    question = (message.text or '').strip()
    if len(question) < 3:
        await message.answer('Сформулируйте вопрос чуть подробнее.')
        return
    async with async_session_factory() as session:
        user = await get_user(session, message.from_user.id)
        birth_info = _birth_info_from_user(user)
        if birth_info is None:
            await message.answer('Сначала заполните данные рождения через /start.')
            await state.clear()
            return
        chart = calculate_natal_chart(birth_info)
        reading = await generate_question_reading(chart, question, user.first_name)
        await create_reading(session, message.from_user.id, 'question', reading, question=question)
    await state.clear()
    await message.answer(reading)


@router.message(Command('compatibility'))
async def compatibility_command(message: Message, state: FSMContext) -> None:
    await state.set_state(InteractionStates.waiting_for_partner_data)
    await message.answer('Отправьте данные партнера в формате:\nИмя; YYYY-MM-DD; HH:MM или примерно; Город\n\nПример: Алекс; 1992-10-01; 08:15; Казань')


@router.message(InteractionStates.waiting_for_partner_data)
async def receive_partner_data(message: Message, state: FSMContext) -> None:
    payload = [part.strip() for part in (message.text or '').split(';')]
    if len(payload) != 4:
        await message.answer('Нужны 4 части через точку с запятой: Имя; YYYY-MM-DD; HH:MM или примерно; Город')
        return
    partner_name, birth_date_raw, birth_time_raw, place_query = payload
    try:
        partner_date = date.fromisoformat(birth_date_raw)
    except ValueError:
        await message.answer('Дата должна быть в формате YYYY-MM-DD.')
        return
    partner_time = None
    approximate = birth_time_raw.lower() in {'примерно', 'не знаю', 'approx'}
    if not approximate:
        try:
            partner_time = time.fromisoformat(birth_time_raw)
        except ValueError:
            await message.answer('Время должно быть в формате HH:MM или словом «примерно».')
            return
    places = await search_places(place_query, limit=1)
    if not places:
        await message.answer('Не удалось найти город партнера.')
        return
    place = places[0]
    async with async_session_factory() as session:
        user = await get_user(session, message.from_user.id)
        birth_info = _birth_info_from_user(user)
        if birth_info is None:
            await message.answer('Сначала заполните свои данные через /start.')
            await state.clear()
            return
        user_chart = calculate_natal_chart(birth_info)
        partner_chart = calculate_natal_chart(
            BirthInfo(
                birth_date=partner_date,
                birth_time=partner_time,
                latitude=place['latitude'],
                longitude=place['longitude'],
                timezone=place['timezone'],
                birth_place=place['name'],
                is_time_approximate=approximate,
            )
        )
        report = calculate_compatibility(user_chart, partner_chart, partner_name)
        reading = await generate_compatibility_reading(report, partner_name)
        await create_reading(session, message.from_user.id, 'compatibility', reading, question=partner_name)
    await state.clear()
    await message.answer(reading)
