import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.bot.handlers import setup_routers
from app.bot.middlewares import DatabaseMiddleware
from app.config import get_settings
from app.database import init_db
from app.webapp.api.routes import router as webapp_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

def _create_bot() -> Bot:
    token = settings.bot_token
    if not token:
        token = "0:DEV"
    return Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

bot = _create_bot()
dp = Dispatcher()
dp.update.middleware(DatabaseMiddleware())
dp.include_router(setup_routers())


BOT_COMMANDS = [
    BotCommand(command="start", description="Приветствие и регистрация"),
    BotCommand(command="chart", description="Натальная карта"),
    BotCommand(command="today", description="Прогноз на сегодня"),
    BotCommand(command="week", description="Прогноз на неделю (Premium)"),
    BotCommand(command="compatibility", description="Совместимость"),
    BotCommand(command="ask", description="Вопрос астрологу"),
    BotCommand(command="transit", description="Транзиты (Premium)"),
    BotCommand(command="settings", description="Настройки и подписка"),
    BotCommand(command="help", description="Справка"),
    BotCommand(command="privacy", description="Политика конфиденциальности"),
    BotCommand(command="my_data", description="Мои данные"),
    BotCommand(command="delete_data", description="Удалить данные"),
    BotCommand(command="export_data", description="Экспорт данных"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await bot.set_my_commands(BOT_COMMANDS)
    if settings.webhook_url:
        await bot.set_webhook(settings.full_webhook_url)
        logger.info("Webhook set to %s", settings.full_webhook_url)
    else:
        logger.info("WEBHOOK_URL not set — use polling mode via python -m app.polling")
    yield
    await bot.session.close()


app = FastAPI(title="Stellarium AI", lifespan=lifespan)
app.include_router(webapp_router)
app.mount("/app/static", StaticFiles(directory="app/webapp/static"), name="static")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "stellarium-ai"}


@app.post(settings.webhook_path)
async def webhook(request: Request):
    from aiogram.types import Update

    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/")
async def root():
    return {
        "service": "Stellarium AI",
        "docs": "/docs",
        "mini_app": "/app",
        "health": "/health",
    }
