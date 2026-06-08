"""Resolve or create the ``User`` row for every incoming update."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.database import crud


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session = data.get("session")
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user
        else:
            tg_user = getattr(event, "from_user", None)

        if session is not None and tg_user is not None:
            user = await crud.get_or_create_user(
                session,
                telegram_id=tg_user.id,
                first_name=tg_user.first_name,
                username=tg_user.username,
                language_code=tg_user.language_code,
            )
            data["user"] = user
        return await handler(event, data)
