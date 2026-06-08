import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.bot.handlers import commands, data_rights, inline_mode, onboarding, payments
from app.config import Settings

logger = logging.getLogger(__name__)


def create_bot(settings: Settings) -> Bot:
    return Bot(
        token=settings.require_bot_token(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(onboarding.router)
    dispatcher.include_router(commands.router)
    dispatcher.include_router(payments.router)
    dispatcher.include_router(data_rights.router)
    dispatcher.include_router(inline_mode.router)
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
            BotCommand(command="help", description="Справка по командам"),
            BotCommand(command="privacy", description="Политика конфиденциальности"),
            BotCommand(command="my_data", description="Показать сохраненные данные"),
            BotCommand(command="export_data", description="Экспорт данных"),
            BotCommand(command="delete_data", description="Удалить аккаунт"),
        ]
    )
