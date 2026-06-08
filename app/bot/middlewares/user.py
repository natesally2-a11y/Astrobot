"""Ensure a User record exists for every incoming update."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User as TgUser

from app.database.crud import get_or_create_user


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user is None and isinstance(event, (Message, CallbackQuery)):
            tg_user = event.from_user

        if tg_user is not None and tg_user.id:
            session = data.get("session")
            if session is not None:
                user, _created = await get_or_create_user(
                    session,
                    telegram_id=tg_user.id,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    username=tg_user.username,
                    language_code=tg_user.language_code,
                )
                data["user"] = user
        return await handler(event, data)
