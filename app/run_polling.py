"""Запуск бота в режиме long-polling без веб-сервера (для разработки).

Использование:  python -m app.run_polling
"""
from __future__ import annotations

import asyncio
import logging

from app.bot.bot import create_bot, create_dispatcher
from app.bot.commands import set_bot_commands
from app.config import settings
from app.database import init_models

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


async def main() -> None:
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN не задан. Заполните .env")

    await init_models()
    bot = create_bot()
    dp = create_dispatcher()
    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
