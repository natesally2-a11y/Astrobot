from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from redis.asyncio import Redis

from app.bot.handlers.core import router
from app.bot.middlewares.database import DatabaseSessionMiddleware
from app.config import get_settings


def create_bot() -> Bot:
    settings = get_settings()
    return Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    settings = get_settings()
    try:
        redis = Redis.from_url(settings.redis_url)
        storage = RedisStorage(redis=redis)
    except Exception:
        storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)
    dispatcher.update.middleware(DatabaseSessionMiddleware())
    dispatcher.include_router(router)
    return dispatcher


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Приветствие и регистрация"),
            BotCommand(command="chart", description="Показать натальную карту"),
            BotCommand(command="today", description="Персональный прогноз на сегодня"),
            BotCommand(command="week", description="Прогноз на неделю (Premium)"),
            BotCommand(command="compatibility", description="Совместимость с партнером"),
            BotCommand(command="ask", description="Задать вопрос астрологу"),
            BotCommand(command="transit", description="Важные транзиты (Premium)"),
            BotCommand(command="settings", description="Настройки и подписка"),
            BotCommand(command="privacy", description="Политика конфиденциальности"),
            BotCommand(command="my_data", description="Показать сохраненные данные"),
            BotCommand(command="export_data", description="Экспорт данных в JSON"),
            BotCommand(command="delete_data", description="Удалить аккаунт и данные"),
            BotCommand(command="help", description="Справка"),
        ]
    )
