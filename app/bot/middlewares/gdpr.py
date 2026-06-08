"""GDPR consent middleware — blocks data-sensitive operations until consent is given."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.database.crud import get_user

EXEMPT_COMMANDS = {"/start", "/help", "/privacy", "/delete_data"}


class GDPRMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id: int | None = None

        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            if event.text and any(event.text.startswith(cmd) for cmd in EXEMPT_COMMANDS):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            if event.data and event.data.startswith(("gdpr_", "privacy_", "about_")):
                return await handler(event, data)

        if user_id:
            user = await get_user(user_id)
            if user and not user.gdpr_consent:
                if isinstance(event, Message) and event.text and not event.text.startswith("/"):
                    pass
                elif isinstance(event, CallbackQuery) and event.data == "gdpr_accept":
                    return await handler(event, data)

        return await handler(event, data)
