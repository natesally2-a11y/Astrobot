"""Фабрика бота и диспетчера aiogram."""
from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import register_handlers
from app.bot.middlewares import DbSessionMiddleware
from app.config import settings

logger = logging.getLogger(__name__)


def _build_storage():
    """FSM-хранилище: Redis, если доступен, иначе in-memory."""
    if settings.redis_url:
        try:
            from aiogram.fsm.storage.redis import RedisStorage

            return RedisStorage.from_url(settings.redis_url)
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis storage unavailable (%s), using memory", exc)
    return MemoryStorage()


def create_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=_build_storage())

    db_mw = DbSessionMiddleware()
    dp.message.middleware(db_mw)
    dp.callback_query.middleware(db_mw)
    dp.pre_checkout_query.middleware(db_mw)

    register_handlers(dp)
    return dp
