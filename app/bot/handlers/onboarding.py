from datetime import date, datetime, time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.calendar import build_calendar
from app.bot.keyboards.menus import place_choices_keyboard
from app.bot.states import OnboardingStates
from app.database.crud import save_birth_data, set_gdpr_consent, upsert_user
from app.database.session import async_session_factory
from app.services.geocoding import search_places

router = Router(name='onboarding')


@router.callback_query(F.data == 'gdpr:agree')
async def agree_gdpr(callback: CallbackQuery, state: FSMContext) -> None:
    async with async_session_factory() as session:
        await upsert_user(session, callback.from_user.id, callback.from_user.first_name, callback.from_user.username)
        await set_gdpr_consent(session, callback.from_user.id, True)
    await state.set_state(OnboardingStates.waiting_for_birth_date)
    await callback.message.answer('Отлично. Выберите дату рождения в календаре:', reply_markup=build_calendar())
    await callback.answer('Согласие сохранено')


@router.message(Command('chart_setup'))
async def chart_setup(message: Message, state: FSMContext) -> None:
    async with async_session_factory() as session:
        await upsert_user(session, message.from_user.id, message.from_user.first_name, message.from_user.username)
    await state.set_state(OnboardingStates.waiting_for_birth_date)
    await message.answer('Выберите дату рождения:', reply_markup=build_calendar())


@router.callback_query(F.data == 'noop')
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith('calendar:nav:'))
async def calendar_nav(callback: CallbackQuery) -> None:
    _, _, year, month = callback.data.split(':')
    await callback.message.edit_reply_markup(reply_markup=build_calendar(int(year), int(month)))
    await callback.answer()


@router.callback_query(F.data.startswith('calendar:pick:'))
async def calendar_pick(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, year, month, day = callback.data.split(':')
    selected_date = date(int(year), int(month), int(day))
    await state.update_data(birth_date=selected_date.isoformat())
    await state.set_state(OnboardingStates.waiting_for_birth_time)
    await callback.message.answer('Введите время рождения в формате HH:MM. Если знаете только примерно, отправьте «примерно».')
    await callback.answer(f'Дата выбрана: {selected_date.isoformat()}')


@router.message(OnboardingStates.waiting_for_birth_time)
async def receive_time(message: Message, state: FSMContext) -> None:
    raw = (message.text or '').strip().lower()
    approximate = raw in {'примерно', 'не знаю', 'unknown', 'approx'}
    parsed_time = None
    if not approximate:
        try:
            parsed_time = datetime.strptime(raw, '%H:%M').time()
        except ValueError:
            await message.answer('Не смог распознать время. Используйте формат HH:MM или отправьте «примерно».')
            return
    await state.update_data(birth_time=parsed_time.isoformat(timespec='minutes') if parsed_time else None, is_time_approximate=approximate)
    await state.set_state(OnboardingStates.waiting_for_birth_place)
    await message.answer('Теперь напишите город рождения. Я найду варианты через OpenStreetMap/Nominatim.')


@router.message(OnboardingStates.waiting_for_birth_place)
async def receive_place(message: Message, state: FSMContext) -> None:
    query = (message.text or '').strip()
    results = await search_places(query)
    if not results:
        await message.answer('Не удалось найти подходящие города. Попробуйте написать иначе, например: Москва, Россия.')
        return
    await state.update_data(place_options=results)
    await state.set_state(OnboardingStates.waiting_for_place_choice)
    await message.answer('Выберите подходящий вариант:', reply_markup=place_choices_keyboard(results))


@router.callback_query(OnboardingStates.waiting_for_place_choice, F.data == 'place:retry')
async def retry_place(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.waiting_for_birth_place)
    await callback.message.answer('Хорошо, введите город еще раз.')
    await callback.answer()


@router.callback_query(OnboardingStates.waiting_for_place_choice, F.data.startswith('place:'))
async def choose_place(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data == 'place:retry':
        return
    index = int(callback.data.split(':')[1])
    data = await state.get_data()
    options = data.get('place_options', [])
    if index >= len(options):
        await callback.answer('Этот вариант уже устарел, попробуйте поиск снова.', show_alert=True)
        return
    place = options[index]
    birth_date = date.fromisoformat(data['birth_date'])
    birth_time = time.fromisoformat(data['birth_time']) if data.get('birth_time') else None
    async with async_session_factory() as session:
        await save_birth_data(
            session=session,
            telegram_id=callback.from_user.id,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=place['name'],
            latitude=place['latitude'],
            longitude=place['longitude'],
            timezone_name=place['timezone'],
            is_time_approximate=bool(data.get('is_time_approximate')),
        )
    await state.clear()
    await callback.message.answer('✨ Натальные данные сохранены. Теперь можно использовать /chart, /today и /ask.')
    await callback.answer('Карта сохранена')
