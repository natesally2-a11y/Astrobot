"""Stellarium AI entry point.

Combines:
  * FastAPI server (Mini App + REST API + webhook receiver)
  * aiogram bot dispatcher (handlers, FSM storage, middlewares)

Two run modes:
  * Long polling (default for development)
  * Webhook (set ``USE_WEBHOOK=true`` and provide ``WEBHOOK_URL``)
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    MenuButtonWebApp,
    Update,
    WebAppInfo,
)
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.bot.handlers import get_router
from app.bot.middlewares.db import DatabaseMiddleware
from app.bot.middlewares.user import UserMiddleware
from app.config import PROJECT_ROOT, settings
from app.database import init_db
from app.webapp.api.routes import router as api_router

logger = logging.getLogger(__name__)


def _build_dispatcher() -> Dispatcher:
    storage = MemoryStorage()
    try:
        if settings.redis_url:
            from aiogram.fsm.storage.redis import RedisStorage
            storage = RedisStorage.from_url(settings.redis_url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falling back to in-memory FSM storage: %s", exc)

    dp = Dispatcher(storage=storage)
    dp.update.outer_middleware(DatabaseMiddleware())
    dp.update.outer_middleware(UserMiddleware())
    dp.include_router(get_router())
    return dp


def _build_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


COMMANDS = [
    BotCommand(command="start", description="Приветствие и регистрация"),
    BotCommand(command="chart", description="Натальная карта"),
    BotCommand(command="today", description="Прогноз на сегодня"),
    BotCommand(command="week", description="Прогноз на неделю (Pro)"),
    BotCommand(command="compatibility", description="Совместимость с партнёром"),
    BotCommand(command="ask", description="Задать вопрос астрологу"),
    BotCommand(command="transit", description="Важные транзиты (Pro)"),
    BotCommand(command="settings", description="Настройки и подписка"),
    BotCommand(command="privacy", description="Политика конфиденциальности"),
    BotCommand(command="my_data", description="Показать мои данные"),
    BotCommand(command="export_data", description="Экспортировать данные"),
    BotCommand(command="delete_data", description="Удалить аккаунт"),
    BotCommand(command="help", description="Справка по командам"),
]


async def _set_commands(bot: Bot) -> None:
    try:
        await bot.set_my_commands(COMMANDS, scope=BotCommandScopeAllPrivateChats())
    except Exception:
        logger.exception("Failed to set bot commands")


async def _set_menu_button(bot: Bot) -> None:
    if not settings.webapp_url:
        return
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🌌 Stellarium",
                web_app=WebAppInfo(url=settings.webapp_url),
            )
        )
    except Exception:
        logger.exception("Failed to set chat menu button")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )

    try:
        await init_db()
    except Exception:
        logger.exception("Database init failed — continuing, fix DATABASE_URL")

    bot: Bot | None = None
    dp: Dispatcher | None = None
    polling_task: asyncio.Task | None = None

    if not settings.bot_token:
        logger.warning("BOT_TOKEN is empty — running without the Telegram bot")
    else:
        bot = _build_bot()
        dp = _build_dispatcher()
        await _set_commands(bot)
        await _set_menu_button(bot)

        if settings.use_webhook and settings.full_webhook_url:
            await bot.set_webhook(
                settings.full_webhook_url,
                drop_pending_updates=True,
                allowed_updates=dp.resolve_used_update_types(),
            )
            logger.info("Webhook set: %s", settings.full_webhook_url)
        else:
            await bot.delete_webhook(drop_pending_updates=True)
            polling_task = asyncio.create_task(
                dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
            )
            logger.info("Bot polling started")

    app.state.bot = bot
    app.state.dp = dp

    try:
        yield
    finally:
        if polling_task is not None:
            polling_task.cancel()
            try:
                await polling_task
            except (asyncio.CancelledError, Exception):
                pass
        if bot is not None:
            try:
                if settings.use_webhook:
                    await bot.delete_webhook()
            finally:
                await bot.session.close()


app = FastAPI(
    title="Stellarium AI",
    version="0.1.0",
    description="Telegram astrology bot + Mini App.",
    lifespan=lifespan,
)

app.include_router(api_router)

STATIC_DIR = PROJECT_ROOT / "app" / "webapp" / "static"
TEMPLATES_DIR = PROJECT_ROOT / "app" / "webapp" / "templates"
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


@app.get("/")
async def root_index() -> dict:
    return {
        "service": "Stellarium AI",
        "status": "running",
        "miniapp": "/app",
        "docs": "/docs",
    }


@app.get("/app", include_in_schema=False)
async def miniapp_index() -> FileResponse:
    return FileResponse(TEMPLATES_DIR / "app.html")


@app.get("/health", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok"}


@app.post("/webhook/{secret}", include_in_schema=False)
async def telegram_webhook(secret: str, request: Request) -> Response:
    if secret != settings.webhook_secret:
        return JSONResponse({"detail": "forbidden"}, status_code=403)
    bot: Bot | None = app.state.bot
    dp: Dispatcher | None = app.state.dp
    if bot is None or dp is None:
        return JSONResponse({"detail": "bot not configured"}, status_code=503)
    payload = await request.json()
    update = Update.model_validate(payload, context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=200)
