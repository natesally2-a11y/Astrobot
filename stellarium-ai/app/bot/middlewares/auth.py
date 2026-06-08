from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.database.connection import async_session_factory
from app.database import crud


class DatabaseMiddleware(BaseMiddleware):
    """Inject database session and user into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["session"] = session

            user_obj = None
            if isinstance(event, (Message, CallbackQuery)):
                tg_user = event.from_user
                if tg_user:
                    user_obj, is_new = await crud.get_or_create_user(
                        session,
                        telegram_id=tg_user.id,
                        first_name=tg_user.first_name,
                        last_name=tg_user.last_name,
                        username=tg_user.username,
                        language_code=tg_user.language_code,
                    )

            data["db_user"] = user_obj
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
