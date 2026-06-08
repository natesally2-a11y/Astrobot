"""FastAPI app that hosts the Mini App and (optionally) Telegram webhook."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.bot.bot_setup import configure_bot, create_bot, create_dispatcher
from app.config import get_settings
from app.database import init_db
from app.webapp.api import router as api_router
from app.webapp.views import router as views_router


settings = get_settings()
bot = create_bot()
dispatcher = create_dispatcher()

_polling_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await configure_bot(bot)

    global _polling_task
    if settings.use_webhook:
        webhook_url = settings.webhook_url.rstrip("/") + settings.webhook_path
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.webhook_secret,
            drop_pending_updates=True,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
        logger.info("Webhook configured: {}", webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        _polling_task = asyncio.create_task(_run_polling())
        logger.info("Polling started")

    try:
        yield
    finally:
        if _polling_task is not None:
            _polling_task.cancel()
            try:
                await _polling_task
            except (asyncio.CancelledError, Exception):
                pass
        await bot.session.close()


async def _run_polling() -> None:
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Polling crashed: {}", exc)


app = FastAPI(title="Stellarium AI", version="0.1.0", lifespan=lifespan)
app.include_router(views_router)
app.include_router(api_router)

STATIC_DIR = Path(__file__).parent / "webapp" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.post(settings.webhook_path)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if settings.webhook_secret and x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(status_code=401, detail="invalid secret token")
    body = await request.json()
    update = Update.model_validate(body, context={"bot": bot})
    await dispatcher.feed_update(bot=bot, update=update)
    return {"ok": True}
