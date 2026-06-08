"""Main entry point — FastAPI application with aiogram webhook and Mini App."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update, BotCommand

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

from app.webapp.api.routes import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

templates = Jinja2Templates(directory="app/webapp/templates")


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Stellarium AI...")
    await init_db()

    await bot.set_my_commands(BOT_COMMANDS)

    if settings.webhook_url:
        webhook = f"{settings.webhook_url}{settings.webhook_path}"
        await bot.set_webhook(webhook, drop_pending_updates=True)
        logger.info(f"Webhook set: {webhook}")
    else:
        logger.info("No WEBHOOK_URL set — use polling mode via run_polling.py")

    yield

    if settings.webhook_url:
        await bot.delete_webhook()
    await bot.session.close()
    await close_db()
    logger.info("Stellarium AI stopped.")


app = FastAPI(title="Stellarium AI", lifespan=lifespan)

app.mount("/app/static", StaticFiles(directory="app/webapp/static"), name="static")

app.include_router(api_router)


@app.post(settings.webhook_path)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/app", response_class=HTMLResponse)
async def webapp_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok", "service": "stellarium-ai"}
