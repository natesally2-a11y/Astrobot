"""Standalone script for running the bot in long-polling mode.

Useful for local dev — `python run_bot.py`. The FastAPI app (`app/main.py`)
handles polling on its own when ``WEBHOOK_URL`` is not set; this script is
provided for users who don't need the HTTP server at all.
"""
from __future__ import annotations

import asyncio

from loguru import logger

from app.bot.bot_setup import configure_bot, create_bot, create_dispatcher
from app.database import init_db


async def main() -> None:
    bot = create_bot()
    dp = create_dispatcher()
    await init_db()
    await configure_bot(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Starting long polling…")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
