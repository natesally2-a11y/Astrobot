import json

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.bot.keyboards.menus import consent_keyboard, onboarding_start_keyboard, settings_keyboard
from app.bot.states import InteractionStates
from app.bot.utils.formatting import CONSENT_TEXT, DISCLAIMER_TEXT, HELP_TEXT
from app.config import settings
from app.database.crud import delete_user_data, export_user_bundle, get_user, upsert_user
from app.database.session import async_session_factory

router = Router(name='common')


@router.message(CommandStart())
async def start(message: Message) -> None:
    async with async_session_factory() as session:
        await upsert_user(session, message.from_user.id, message.from_user.first_name, message.from_user.username)
    text = (
        '👋 <b>Добро пожаловать в Stellarium AI!</b>\n\n'
        'Я — ваш персональный ИИ-астролог. Создам точную натальную карту и буду давать прогнозы, основанные именно на вашей карте, а не на общих гороскопах.\n\n'
        'Для начала мне нужны данные рождения:\n'
        '📅 дата рождения\n'
        '⏰ время рождения (хотя бы примерное)\n'
        '📍 место рождения'
    )
    await message.answer(text, reply_markup=onboarding_start_keyboard())
    await message.answer(DISCLAIMER_TEXT)


@router.callback_query(F.data == 'onboarding:start')
async def start_onboarding(callback: CallbackQuery) -> None:
    await callback.message.answer(CONSENT_TEXT, reply_markup=consent_keyboard())
    await callback.answer()


@router.message(Command('help'))
async def help_command(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command('privacy'))
async def privacy_command(message: Message) -> None:
    await message.answer(f'Политика конфиденциальности: {settings.app_base_url.rstrip("/")}/privacy\n\n' + DISCLAIMER_TEXT)


@router.message(Command('my_data'))
async def my_data(message: Message) -> None:
    async with async_session_factory() as session:
        user = await get_user(session, message.from_user.id)
        if user is None:
            await message.answer('Профиль пока не создан. Нажмите /start.')
            return
        data = await export_user_bundle(session, message.from_user.id)
    summary = json.dumps(data, ensure_ascii=False, indent=2)[:3900]
    await message.answer(f'<pre>{summary}</pre>')


@router.message(Command('export_data'))
async def export_data(message: Message) -> None:
    async with async_session_factory() as session:
        user = await get_user(session, message.from_user.id)
        if user is None:
            await message.answer('Нет данных для экспорта.')
            return
        data = await export_user_bundle(session, message.from_user.id)
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    await message.answer_document(BufferedInputFile(payload, filename='stellarium_export.json'))


@router.message(Command('delete_data'))
async def delete_data(message: Message, state: FSMContext) -> None:
    await state.set_state(InteractionStates.waiting_for_delete_confirmation)
    await message.answer('Введите слово DELETE, чтобы полностью удалить аккаунт и все данные.')


@router.message(InteractionStates.waiting_for_delete_confirmation)
async def confirm_delete(message: Message, state: FSMContext) -> None:
    if (message.text or '').strip().upper() != 'DELETE':
        await message.answer('Удаление отменено. Для подтверждения отправьте ровно DELETE.')
        return
    async with async_session_factory() as session:
        await delete_user_data(session, message.from_user.id)
    await state.clear()
    await message.answer('Все данные удалены. Если захотите вернуться, нажмите /start.')


@router.message(Command('settings'))
async def settings_command(message: Message) -> None:
    async with async_session_factory() as session:
        user = await get_user(session, message.from_user.id)
        if user is None:
            await upsert_user(session, message.from_user.id, message.from_user.first_name, message.from_user.username)
            user = await get_user(session, message.from_user.id)
    subscription = user.subscription_type if user else 'free'
    expires = user.subscription_expires_at.isoformat() if user and user.subscription_expires_at else '—'
    await message.answer(
        f'⚙️ <b>Настройки Stellarium AI</b>\n\nТариф: <b>{subscription}</b>\nДействует до: {expires}',
        reply_markup=settings_keyboard(message.from_user.id),
    )
