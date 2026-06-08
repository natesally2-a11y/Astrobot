from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.bot.bot_app import start_bot_polling_task, stop_bot_polling_task
from app.config import get_settings
from app.database.session import init_db
from app.webapp.routes import router as webapp_router

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    if settings.run_bot_polling:
        logger.info("Starting Telegram bot polling in background task")
        start_bot_polling_task()
    yield
    await stop_bot_polling_task()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(webapp_router)
app.mount("/static", StaticFiles(directory="app/webapp/static"), name="static")

