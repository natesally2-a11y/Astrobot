import asyncio

from app.bot.runtime import bot, dp, set_commands
from app.database.database import init_db


async def main() -> None:
    await init_db()
    await set_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
