"""
Stellarium AI — Main entry point.
Combines FastAPI (web server + Mini App) with aiogram (Telegram bot).
Supports both webhook (production) and polling (development) modes.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.connection import init_db
from app.bot.middlewares.auth import DatabaseMiddleware
from app.bot.handlers import (
    start, chart, today, week, compatibility, ask,
    transit, settings as settings_handler, payments, privacy, inline_mode,
)
from app.webapp.routes import router as webapp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    try:
        if settings.REDIS_URL:
            from redis.asyncio import Redis
            redis = Redis.from_url(settings.REDIS_URL)
            storage = RedisStorage(redis)
        else:
            storage = MemoryStorage()
    except Exception:
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)

    dp.update.middleware(DatabaseMiddleware())

    dp.include_router(start.router)
    dp.include_router(chart.router)
    dp.include_router(today.router)
    dp.include_router(week.router)
    dp.include_router(compatibility.router)
    dp.include_router(ask.router)
    dp.include_router(transit.router)
    dp.include_router(settings_handler.router)
    dp.include_router(payments.router)
    dp.include_router(privacy.router)
    dp.include_router(inline_mode.router)

    return dp


bot = create_bot()
dp = create_dispatcher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Stellarium AI...")
    await init_db()
    logger.info("Database initialized")

    if settings.WEBHOOK_URL:
        webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info(f"Webhook set: {webhook_url}")
    else:
        logger.info("Running in polling mode (no WEBHOOK_URL set)")
        asyncio.create_task(_run_polling())

    yield

    if settings.WEBHOOK_URL:
        await bot.delete_webhook()

    await bot.session.close()
    logger.info("Stellarium AI stopped")


async def _run_polling():
    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Polling error: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Stellarium AI",
        description="Personal AI Astrologer Telegram Bot",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.WEBHOOK_URL:
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler
        from aiogram.webhook.fastapi_server import FastAPIMultipleRequestHandler

        @app.post(settings.WEBHOOK_PATH)
        async def webhook_handler(request):
            from aiogram.types import Update
            import json
            body = await request.body()
            update = Update.model_validate_json(body)
            await dp.feed_update(bot, update)

    app.include_router(webapp_router)

    try:
        app.mount("/static", StaticFiles(directory="app/webapp/static"), name="static")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
        log_level="info",
    )
