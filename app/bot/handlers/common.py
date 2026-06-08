"""Общие помощники обработчиков."""
from __future__ import annotations

from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.calculations import NatalChart
from app.bot import texts
from app.bot.keyboards.common import start_keyboard
from app.database import crud
from app.database.models import User
from app.plans import is_premium
from app.services.chart_service import chart_from_birth_data


async def require_chart(
    message: Message, session: AsyncSession, user_id: int
) -> NatalChart | None:
    """Вернуть натальную карту пользователя или подсказать создать её."""
    user = await crud.get_user(session, user_id)
    if not user or not user.gdpr_consent:
        await message.answer(texts.NEED_CONSENT)
        return None
    bd = await crud.get_birth_data(session, user_id)
    if bd is None:
        await message.answer(texts.NEED_BIRTH_DATA, reply_markup=start_keyboard())
        return None
    return chart_from_birth_data(bd)


async def require_premium(
    message: Message, session: AsyncSession, user_id: int
) -> bool:
    user = await crud.get_user(session, user_id)
    if user and is_premium(user.subscription_type) and crud.is_subscription_active(user):
        return True
    await message.answer(texts.PREMIUM_ONLY)
    return False


def event_message(event: Message | CallbackQuery) -> Message:
    return event if isinstance(event, Message) else event.message
