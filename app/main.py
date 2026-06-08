"""FastAPI application entrypoint.

Serves the Mini App + REST API and integrates the Telegram bot in either
webhook mode (production) or polling mode (local development).
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

from app.bot.bot import create_bot, create_dispatcher, set_bot_commands
from app.config import settings
from app.database.base import init_db
from app.webapp.api.routes import router as api_router
from app.webapp.routes import router as webapp_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("stellarium")

bot = create_bot()
dp = create_dispatcher()
_polling_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _polling_task
    await init_db()

    try:
        await set_bot_commands(bot)
    except Exception as exc:
        logger.warning("Could not set bot commands: %s", exc)

    # Bot setup is best-effort: a bad/unreachable token must not stop the web
    # server (the Mini App should keep serving regardless).
    try:
        if settings.is_webhook and settings.webhook_url:
            await bot.set_webhook(
                url=settings.webhook_full_url,
                secret_token=settings.webhook_secret or None,
                drop_pending_updates=True,
                allowed_updates=dp.resolve_used_update_types(),
            )
            logger.info("Webhook set to %s", settings.webhook_full_url)
        else:
            await bot.delete_webhook(drop_pending_updates=True)
            _polling_task = asyncio.create_task(_run_polling())
            logger.info("Started bot in polling mode.")
    except Exception as exc:
        logger.error("Bot startup failed (%s). Web server continues running.", exc)

    yield

    if _polling_task:
        _polling_task.cancel()
    await bot.session.close()


async def _run_polling() -> None:
    try:
        await dp.start_polling(bot, handle_signals=False)
    except asyncio.CancelledError:  # pragma: no cover
        pass
    except Exception as exc:  # pragma: no cover
        logger.exception("Polling loop crashed: %s", exc)


app = FastAPI(title="Stellarium AI", version="1.0.0", lifespan=lifespan)

# Static assets & routers.
app.mount("/static", StaticFiles(directory="app/webapp/static"), name="static")
app.include_router(webapp_router)
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "stellarium-ai"}


@app.post(settings.webhook_path)
async def telegram_webhook(request: Request) -> Response:
    """Receive updates from Telegram (webhook mode)."""
    if settings.webhook_secret:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if header != settings.webhook_secret:
            return Response(status_code=403)
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=200)
