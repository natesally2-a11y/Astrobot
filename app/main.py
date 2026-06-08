import logging
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.bot.setup import create_bot, create_dispatcher, set_bot_commands
from app.config import get_settings
from app.database.session import init_db
from app.webapp.api.routes import router as webapp_api_router

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

bot = create_bot(settings) if settings.bot_token else None
dispatcher = create_dispatcher() if bot else None
templates = Jinja2Templates(directory="app/webapp/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if bot and dispatcher:
        await set_bot_commands(bot)
        if settings.webhook_url:
            await bot.set_webhook(settings.webhook_url)
            logger.info("Telegram webhook configured.")
        else:
            logger.warning("WEBHOOK_URL is not set; Telegram webhook was not configured.")
    yield
    if bot:
        await bot.session.close()


app = FastAPI(
    title="Stellarium AI",
    description="Telegram AI astrologer bot and Mini App",
    version="0.1.0",
    lifespan=lifespan,
)
app.mount("/app/static", StaticFiles(directory="app/webapp/static"), name="webapp-static")
app.include_router(webapp_api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict[str, bool]:
    if bot is None or dispatcher is None:
        return {"ok": False}
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dispatcher.feed_update(bot, update)
    return {"ok": True}


@app.get("/app", response_class=HTMLResponse)
async def mini_app(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})
