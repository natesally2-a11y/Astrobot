"""Точка входа: FastAPI-приложение + Telegram-бот (webhook или polling)."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.bot.bot import create_bot, create_dispatcher
from app.bot.commands import set_bot_commands
from app.config import settings
from app.database import init_models
from app.webapp.api import router as api_router
from app.webapp.views import router as views_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("stellarium")

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация БД (создание таблиц для MVP)
    try:
        await init_models()
    except Exception as exc:  # pragma: no cover
        logger.error("DB init failed: %s", exc)

    app.state.bot = None
    app.state.dp = None
    app.state.polling_task = None

    if not settings.bot_token:
        logger.warning("BOT_TOKEN не задан — бот не будет запущен (доступен только Mini App API).")
        yield
        return

    bot = create_bot()
    dp = create_dispatcher()
    app.state.bot = bot
    app.state.dp = dp

    try:
        await set_bot_commands(bot)
    except Exception as exc:  # pragma: no cover
        logger.warning("set_bot_commands failed: %s", exc)

    if settings.use_webhook:
        await bot.set_webhook(
            url=settings.webhook_url,
            secret_token=settings.webhook_secret,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
        logger.info("Webhook установлен: %s", settings.webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        app.state.polling_task = asyncio.create_task(
            dp.start_polling(bot, handle_signals=False)
        )
        logger.info("Бот запущен в режиме polling.")

    yield

    # Завершение
    if app.state.polling_task:
        await dp.stop_polling()
        app.state.polling_task.cancel()
    if settings.use_webhook:
        try:
            await bot.delete_webhook()
        except Exception:  # pragma: no cover
            pass
    await bot.session.close()


app = FastAPI(title="Stellarium AI", version="1.0.0", lifespan=lifespan)

app.mount(
    "/static", StaticFiles(directory=str(BASE_DIR / "webapp" / "static")), name="static"
)
app.include_router(views_router)
app.include_router(api_router)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "version": app.version})


@app.post(settings.webhook_path)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> JSONResponse:
    if not settings.use_webhook or request.app.state.dp is None:
        raise HTTPException(status_code=404, detail="Webhook disabled")
    if x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid secret token")

    data = await request.json()
    update = Update.model_validate(data, context={"bot": request.app.state.bot})
    await request.app.state.dp.feed_update(request.app.state.bot, update)
    return JSONResponse({"ok": True})
