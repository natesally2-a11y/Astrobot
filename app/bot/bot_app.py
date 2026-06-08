from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.bot.handlers.commands import router as commands_router
from app.bot.handlers.inline_mode import router as inline_router
from app.bot.handlers.payments import router as payments_router
from app.bot.handlers.start import router as start_router
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
_polling_task: asyncio.Task | None = None


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(payments_router)
    dp.include_router(commands_router)
    dp.include_router(inline_router)
    return dp


async def _set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запуск и регистрация"),
            BotCommand(command="chart", description="Показать натальную карту"),
            BotCommand(command="today", description="Прогноз на сегодня"),
            BotCommand(command="week", description="Прогноз на неделю (Premium)"),
            BotCommand(command="compatibility", description="Совместимость"),
            BotCommand(command="ask", description="Задать вопрос астрологу"),
            BotCommand(command="transit", description="Важные транзиты (Premium)"),
            BotCommand(command="settings", description="Подписка и настройки"),
            BotCommand(command="help", description="Справка"),
            BotCommand(command="privacy", description="Политика конфиденциальности"),
            BotCommand(command="my_data", description="Показать мои данные"),
            BotCommand(command="delete_data", description="Удалить мои данные"),
            BotCommand(command="export_data", description="Экспорт моих данных"),
        ]
    )


async def run_bot_polling() -> None:
    if not settings.bot_token or "replace-with-bot-token" in settings.bot_token:
        logger.warning("BOT_TOKEN is not configured, polling is skipped.")
        return

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = create_dispatcher()
    await _set_commands(bot)
    await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())


def start_bot_polling_task() -> asyncio.Task:
    global _polling_task
    if _polling_task and not _polling_task.done():
        return _polling_task
    _polling_task = asyncio.create_task(run_bot_polling())
    return _polling_task


async def stop_bot_polling_task() -> None:
    global _polling_task
    if not _polling_task:
        return
    _polling_task.cancel()
    try:
        await _polling_task
    except asyncio.CancelledError:
        pass
    finally:
        _polling_task = None

