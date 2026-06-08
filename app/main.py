from __future__ import annotations

from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.bot.setup import create_bot, create_dispatcher, set_bot_commands
from app.config import get_settings
from app.database.crud import init_models
from app.webapp.router import router as webapp_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()

    bot = create_bot()
    dispatcher = create_dispatcher()
    app.state.bot = bot
    app.state.dispatcher = dispatcher

    if bot is not None:
        await set_bot_commands(bot)
        if settings.webhook_full_url():
            await bot.set_webhook(settings.webhook_full_url())
    yield

    if bot is not None:
        await bot.session.close()


app = FastAPI(
    title="Stellarium AI",
    version="0.1.0",
    description="Telegram bot + Mini App for personal astrology readings.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="app/webapp/static"), name="static")
app.include_router(webapp_router)


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "service": "Stellarium AI",
            "status": "ok",
            "webapp": f"{settings.base_url.rstrip('/')}/app",
            "webhook_configured": bool(settings.webhook_full_url()),
        }
    )


@app.get("/healthz")
async def healthcheck() -> JSONResponse:
    return JSONResponse({"status": "healthy"})


@app.post(settings.webhook_path)
async def telegram_webhook(request: Request) -> JSONResponse:
    bot: Bot | None = request.app.state.bot
    dispatcher: Dispatcher = request.app.state.dispatcher
    if bot is None:
        raise HTTPException(
            status_code=503,
            detail="BOT_TOKEN is not configured. Webhook is unavailable.",
        )

    payload = await request.json()
    update = Update.model_validate(payload, context={"bot": bot})
    await dispatcher.feed_update(bot, update)
    return JSONResponse({"ok": True})
