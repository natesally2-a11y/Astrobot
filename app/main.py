from __future__ import annotations

from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.bot.runtime import bot, dp, set_commands
from app.config import get_settings
from app.database.database import init_db
from app.webapp.api.routes import router as webapp_api_router

settings = get_settings()
templates = Jinja2Templates(directory="app/webapp/templates")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await set_commands()
    if settings.webhook_url:
        await bot.set_webhook(f"{settings.webhook_url.rstrip('/')}/webhook")
    yield
    await bot.delete_webhook(drop_pending_updates=False)
    await bot.session.close()


app = FastAPI(
    title="Stellarium AI",
    description="Telegram bot + mini app backend for astrology MVP",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/app/static", StaticFiles(directory="app/webapp/static"), name="webapp-static")
app.include_router(webapp_api_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(update: dict) -> dict:
    telegram_update = Update.model_validate(update)
    await dp.feed_update(bot, telegram_update)
    return {"ok": True}


@app.get("/app", response_class=HTMLResponse)
async def mini_app(request: Request, user_id: int = 0):
    return templates.TemplateResponse("app.html", {"request": request, "user_id": user_id})
