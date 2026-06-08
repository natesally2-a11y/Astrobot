from __future__ import annotations

import asyncio
import logging

from app.bot.loader import create_bot, create_dispatcher, set_bot_commands
from app.database.session import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = create_bot()
    dispatcher = create_dispatcher()
    try:
        await init_db()
        await set_bot_commands(bot)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Starting Telegram polling")
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
