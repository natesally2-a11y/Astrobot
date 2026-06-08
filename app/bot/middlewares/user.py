"""Middleware that ensures a User row exists and is fresh for each update."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from app.database import crud


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        session = data.get("session")

        if tg_user is not None and session is not None and not tg_user.is_bot:
            user = await crud.get_or_create_user(
                session,
                telegram_id=tg_user.id,
                first_name=tg_user.first_name,
                username=tg_user.username,
                language_code=tg_user.language_code,
            )
            await crud.downgrade_if_expired(session, user)
            data["user"] = user

        return await handler(event, data)
