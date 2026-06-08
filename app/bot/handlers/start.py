from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import DISCLAIMER, main_menu_keyboard, start_keyboard
from app.database import crud

router = Router()

WELCOME_TEXT = """👋 Добро пожаловать в Stellarium AI!

Я — ваш персональный ИИ-астролог. Создам точную натальную карту и буду давать прогнозы, основанные именно на вашей карте, а не на общих гороскопах.

Для начала мне нужны данные рождения:
📅 Дата рождения
⏰ Время рождения (хотя бы примерное)
📍 Место рождения (город)"""


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    referrer_id = None
    if message.text and " " in message.text:
        args = message.text.split(maxsplit=1)[1]
        if args.startswith("ref_"):
            try:
                referrer_id = int(args[4:])
            except ValueError:
                pass

    user = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        referrer_id=referrer_id,
    )

    if referrer_id and user.referrer_id == referrer_id:
        await crud.apply_referral_bonus(session, referrer_id)

    if user.birth_data and user.gdpr_consent:
        await message.answer(
            f"С возвращением, {message.from_user.first_name or 'друг'}! 🌟\n\n"
            f"{DISCLAIMER}",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        f"{WELCOME_TEXT}\n\n{DISCLAIMER}",
        reply_markup=start_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    help_text = """📖 Справка по командам Stellarium AI

/start — Приветствие и регистрация
/chart — Показать натальную карту
/today — Персональный прогноз на сегодня
/week — Прогноз на неделю (Premium)
/compatibility — Совместимость с партнёром
/ask — Задать вопрос астрологу
/transit — Важные транзиты (Premium)
/settings — Настройки и подписка
/privacy — Политика конфиденциальности
/my_data — Показать сохранённые данные
/delete_data — Удалить все данные
/export_data — Экспорт данных в JSON

"""
    await message.answer(help_text + DISCLAIMER)
