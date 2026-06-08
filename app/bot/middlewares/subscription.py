"""Subscription-level check middleware."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.database.crud import check_subscription_level


class SubscriptionMiddleware(BaseMiddleware):
    """Injects `subscription_level` into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id: int | None = None

        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            level = await check_subscription_level(user_id)
            data["subscription_level"] = level
        else:
            data["subscription_level"] = "free"

        return await handler(event, data)
