"""Standalone polling entrypoint: ``python -m app.bot.runner``.

Runs only the Telegram bot (no web server). Useful for local development
when you don't need the Mini App.
"""
from __future__ import annotations

import asyncio
import logging

from app.bot.bot import create_bot, create_dispatcher, set_bot_commands
from app.config import settings
from app.database.base import init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("stellarium.runner")


async def main() -> None:
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")

    await init_db()
    bot = create_bot()
    dp = create_dispatcher()

    try:
        await set_bot_commands(bot)
    except Exception as exc:
        logger.warning("Could not set bot commands: %s", exc)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Stellarium AI bot started (polling).")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
