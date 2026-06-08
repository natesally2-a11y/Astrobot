"""Bot/dispatcher factory shared between webhook and polling modes."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    MenuButtonWebApp,
    WebAppInfo,
)
from loguru import logger

from app.bot.handlers import get_root_router
from app.bot.middlewares import DatabaseMiddleware, UserMiddleware
from app.config import get_settings


def create_bot() -> Bot:
    settings = get_settings()
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    root = get_root_router()
    dp.include_router(root)

    db_mw = DatabaseMiddleware()
    user_mw = UserMiddleware()
    # DB middleware must run before user middleware (user_mw needs the session).
    for observer in (
        dp.message,
        dp.callback_query,
        dp.inline_query,
        dp.pre_checkout_query,
    ):
        observer.middleware(db_mw)
        observer.middleware(user_mw)

    return dp


COMMANDS = [
    BotCommand(command="start", description="Начало работы"),
    BotCommand(command="chart", description="Натальная карта"),
    BotCommand(command="today", description="Прогноз на сегодня"),
    BotCommand(command="week", description="Прогноз на неделю (Pro)"),
    BotCommand(command="compatibility", description="Совместимость"),
    BotCommand(command="ask", description="Спросить астролога"),
    BotCommand(command="transit", description="Транзиты (Pro)"),
    BotCommand(command="settings", description="Настройки и подписка"),
    BotCommand(command="privacy", description="Конфиденциальность"),
    BotCommand(command="my_data", description="Мои данные"),
    BotCommand(command="export_data", description="Экспорт JSON"),
    BotCommand(command="delete_data", description="Удалить аккаунт"),
    BotCommand(command="help", description="Справка"),
]


async def configure_bot(bot: Bot) -> None:
    """Set commands and Mini App menu button."""
    settings = get_settings()
    try:
        await bot.set_my_commands(COMMANDS, scope=BotCommandScopeDefault())
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to set commands: {}", exc)

    if settings.webapp_public_url.startswith("https"):
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="🔭 Открыть",
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to set Mini App menu button: {}", exc)
