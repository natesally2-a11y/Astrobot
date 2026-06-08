"""Run the bot in polling mode (for local development without webhook)."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from app.config import settings
from app.database.session import init_db, close_db

from app.bot.handlers.start import router as start_router
from app.bot.handlers.chart import router as chart_router
from app.bot.handlers.daily import router as daily_router
from app.bot.handlers.compatibility import router as compat_router
from app.bot.handlers.ask import router as ask_router
from app.bot.handlers.transit import router as transit_router
from app.bot.handlers.settings_handler import router as settings_router
from app.bot.handlers.payments import router as payments_router
from app.bot.handlers.inline_mode import router as inline_router

from app.bot.middlewares.gdpr import GDPRMiddleware
from app.bot.middlewares.subscription import SubscriptionMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


BOT_COMMANDS = [
    BotCommand(command="start", description="Приветствие и регистрация"),
    BotCommand(command="chart", description="Показать натальную карту"),
    BotCommand(command="today", description="Персональный прогноз на сегодня"),
    BotCommand(command="week", description="Прогноз на неделю (Pro)"),
    BotCommand(command="compatibility", description="Совместимость с партнёром"),
    BotCommand(command="ask", description="Задать вопрос астрологу"),
    BotCommand(command="transit", description="Важные транзиты (Pro)"),
    BotCommand(command="settings", description="Настройки и подписка"),
    BotCommand(command="help", description="Справка по командам"),
    BotCommand(command="privacy", description="Политика конфиденциальности"),
    BotCommand(command="my_data", description="Показать сохранённые данные"),
    BotCommand(command="export_data", description="Экспорт данных в JSON"),
    BotCommand(command="delete_data", description="Удалить аккаунт"),
]


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    dp.message.middleware(GDPRMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    dp.include_router(start_router)
    dp.include_router(chart_router)
    dp.include_router(daily_router)
    dp.include_router(compat_router)
    dp.include_router(ask_router)
    dp.include_router(transit_router)
    dp.include_router(settings_router)
    dp.include_router(payments_router)
    dp.include_router(inline_router)

    await init_db()
    await bot.set_my_commands(BOT_COMMANDS)

    logger.info("Starting Stellarium AI in polling mode...")
    try:
        await dp.start_polling(bot, drop_pending_updates=True)
    finally:
        await bot.session.close()
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
