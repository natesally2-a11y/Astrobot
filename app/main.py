from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.bot.loader import create_bot, create_dispatcher, set_bot_commands
from app.config import get_settings
from app.database.session import init_db
from app.webapp.api.routes import router as webapp_api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
bot = create_bot()
dispatcher = create_dispatcher()
templates = Jinja2Templates(directory="app/webapp/templates")


async def configure_telegram() -> None:
    try:
        await set_bot_commands(bot)
        logger.info("Telegram bot commands configured")
    except Exception as exc:  # pragma: no cover - network/token dependent
        logger.exception("Could not configure Telegram bot commands: %s", exc)

    if not settings.webhook_url:
        logger.warning("WEBHOOK_URL is not set; run polling locally or configure a public webhook URL")
        return

    try:
        await bot.set_webhook(str(settings.webhook_url), drop_pending_updates=True)
        logger.info("Telegram webhook configured: %s", settings.webhook_url)
    except Exception as exc:  # pragma: no cover - network/token dependent
        logger.exception("Could not configure Telegram webhook: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await configure_telegram()
    try:
        yield
    finally:
        await bot.session.close()


app = FastAPI(title="Stellarium AI", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/webapp/static"), name="static")
app.include_router(webapp_api_router)


@app.get("/health")
async def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "webhook_configured": settings.webhook_url is not None,
        "webapp_configured": settings.webapp_url is not None,
    }


@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict[str, bool]:
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dispatcher.feed_update(bot, update)
    return {"ok": True}


@app.get("/app", response_class=HTMLResponse)
async def mini_app(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "bot_username": settings.bot_username,
        },
    )
