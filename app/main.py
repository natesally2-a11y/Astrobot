from __future__ import annotations

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

settings = get_settings()
bot = create_bot()
dispatcher = create_dispatcher()
templates = Jinja2Templates(directory="app/webapp/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await set_bot_commands(bot)
    if settings.webhook_url:
        await bot.set_webhook(str(settings.webhook_url))
    yield
    await bot.session.close()


app = FastAPI(title="Stellarium AI", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/webapp/static"), name="static")
app.include_router(webapp_api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


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
