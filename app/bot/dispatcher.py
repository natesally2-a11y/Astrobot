from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from app.bot.handlers.common import router as common_router
from app.bot.handlers.inline_mode import router as inline_router
from app.bot.handlers.onboarding import router as onboarding_router
from app.bot.handlers.payments import router as payments_router
from app.bot.handlers.readings import router as readings_router
from app.bot.middlewares.subscription import SubscriptionContextMiddleware
from app.config import settings

COMMANDS = [
    BotCommand(command='start', description='Приветствие и регистрация'),
    BotCommand(command='chart', description='Показать натальную карту'),
    BotCommand(command='today', description='Прогноз на сегодня'),
    BotCommand(command='week', description='Прогноз на неделю'),
    BotCommand(command='compatibility', description='Совместимость с партнером'),
    BotCommand(command='ask', description='Задать вопрос астрологу'),
    BotCommand(command='transit', description='Важные транзиты'),
    BotCommand(command='settings', description='Настройки и подписка'),
    BotCommand(command='help', description='Помощь'),
    BotCommand(command='privacy', description='Политика конфиденциальности'),
    BotCommand(command='my_data', description='Показать мои данные'),
    BotCommand(command='export_data', description='Экспортировать данные'),
    BotCommand(command='delete_data', description='Удалить все данные'),
]


def create_bot() -> Bot | None:
    if not settings.bot_token:
        return None
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.middleware(SubscriptionContextMiddleware())
    dispatcher.include_router(common_router)
    dispatcher.include_router(onboarding_router)
    dispatcher.include_router(readings_router)
    dispatcher.include_router(payments_router)
    dispatcher.include_router(inline_router)
    return dispatcher


async def configure_bot(bot: Bot) -> None:
    await bot.set_my_commands(COMMANDS)
    await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text='Открыть приложение', web_app=WebAppInfo(url=settings.webapp_url)))
    if settings.webhook_url:
        await bot.set_webhook(settings.webhook_url, allowed_updates=['message', 'callback_query', 'inline_query', 'pre_checkout_query'])
