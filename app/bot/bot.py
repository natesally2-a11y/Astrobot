"""Bot & Dispatcher factory."""
from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.bot.handlers import register_handlers
from app.bot.middlewares import DbSessionMiddleware, UserMiddleware
from app.config import settings

logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand(command="start", description="Приветствие и регистрация"),
    BotCommand(command="chart", description="Натальная карта + ИИ-анализ"),
    BotCommand(command="today", description="Прогноз на сегодня"),
    BotCommand(command="week", description="Прогноз на неделю (Premium)"),
    BotCommand(command="compatibility", description="Совместимость с партнёром"),
    BotCommand(command="ask", description="Задать вопрос астрологу"),
    BotCommand(command="transit", description="Важные транзиты (Premium)"),
    BotCommand(command="settings", description="Настройки и подписка"),
    BotCommand(command="privacy", description="Политика конфиденциальности"),
    BotCommand(command="my_data", description="Мои данные"),
    BotCommand(command="export_data", description="Экспорт данных (JSON)"),
    BotCommand(command="delete_data", description="Удалить аккаунт"),
    BotCommand(command="help", description="Справка"),
]


def _build_storage():
    if settings.redis_url:
        try:
            from aiogram.fsm.storage.redis import RedisStorage

            storage = RedisStorage.from_url(settings.redis_url)
            logger.info("Using Redis FSM storage.")
            return storage
        except Exception as exc:  # pragma: no cover - depends on env
            logger.warning("Redis storage unavailable (%s); falling back to memory.", exc)
    logger.info("Using in-memory FSM storage.")
    return MemoryStorage()


def create_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=_build_storage())

    # Outer middlewares: DB session, then user resolution (per update type).
    for observer in (dp.message, dp.callback_query, dp.inline_query, dp.pre_checkout_query):
        observer.outer_middleware(DbSessionMiddleware())
        observer.outer_middleware(UserMiddleware())

    register_handlers(dp)
    return dp


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(BOT_COMMANDS)
