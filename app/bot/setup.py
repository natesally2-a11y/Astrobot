from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.bot.handlers.compatibility import router as compatibility_router
from app.bot.handlers.general import router as general_router
from app.bot.handlers.onboarding import router as onboarding_router
from app.config import get_settings


settings = get_settings()


def create_bot() -> Bot | None:
    if not settings.bot_token:
        return None
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(onboarding_router)
    dispatcher.include_router(compatibility_router)
    dispatcher.include_router(general_router)
    return dispatcher


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Приветствие и регистрация"),
        BotCommand(command="chart", description="Показать натальную карту"),
        BotCommand(command="today", description="Персональный прогноз на сегодня"),
        BotCommand(command="week", description="Прогноз на неделю (Premium)"),
        BotCommand(command="compatibility", description="Совместимость с партнером"),
        BotCommand(command="ask", description="Задать вопрос астрологу"),
        BotCommand(command="transit", description="Важные транзиты (Premium)"),
        BotCommand(command="settings", description="Настройки и подписка"),
        BotCommand(command="privacy", description="Политика конфиденциальности"),
        BotCommand(command="my_data", description="Показать мои данные"),
        BotCommand(command="export_data", description="Экспорт данных"),
        BotCommand(command="delete_data", description="Удаление аккаунта"),
        BotCommand(command="help", description="Справка"),
    ]
    await bot.set_my_commands(commands)
