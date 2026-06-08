from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.crud import get_user
from app.database.session import async_session_factory


class SubscriptionContextMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        telegram_user = data.get('event_from_user')
        if telegram_user:
            async with async_session_factory() as session:
                data['db_user'] = await get_user(session, telegram_user.id)
        return await handler(event, data)
