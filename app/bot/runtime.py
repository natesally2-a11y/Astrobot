from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.bot.handlers import ALL_ROUTERS
from app.bot.middlewares.db import DbSessionMiddleware
from app.config import get_settings

settings = get_settings()

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())

for router in ALL_ROUTERS:
    dp.include_router(router)

db_middleware = DbSessionMiddleware()
dp.message.middleware(db_middleware)
dp.callback_query.middleware(db_middleware)


async def set_commands() -> None:
    commands = [
        BotCommand(command="start", description="Регистрация и старт"),
        BotCommand(command="chart", description="Натальная карта"),
        BotCommand(command="today", description="Прогноз на сегодня"),
        BotCommand(command="week", description="Прогноз на неделю (Premium)"),
        BotCommand(command="compatibility", description="Совместимость"),
        BotCommand(command="ask", description="Задать вопрос астрологу"),
        BotCommand(command="transit", description="Ключевые транзиты (Premium)"),
        BotCommand(command="settings", description="Подписка и настройки"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="privacy", description="Политика конфиденциальности"),
        BotCommand(command="my_data", description="Показать мои данные"),
        BotCommand(command="export_data", description="Экспорт данных"),
        BotCommand(command="delete_data", description="Удалить все данные"),
    ]
    await bot.set_my_commands(commands)
