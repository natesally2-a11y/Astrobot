"""Helpers that gate handlers behind consent / premium / quota."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.database.crud import get_birth_data, has_active_subscription
from app.database.models import BirthData, User


FREE_DAILY_QUESTIONS = 5


async def ensure_consent(user: User, message: Message) -> bool:
    if user.gdpr_consent:
        return True
    await message.answer(texts.NEED_CONSENT)
    return False


async def ensure_birth_data(
    user: User, session: AsyncSession, message: Message
) -> Optional[BirthData]:
    bd = await get_birth_data(session, user.telegram_id)
    if bd is None:
        await message.answer(texts.NEED_BIRTH_DATA)
        return None
    return bd


async def require_premium(
    user: User, message: Message, *, plan: str = "pro"
) -> bool:
    if has_active_subscription(user, plan):
        return True
    await message.answer(texts.PREMIUM_REQUIRED)
    return False


async def spend_free_question(user: User, message: Message) -> bool:
    """For free users, debit a daily quota and short-circuit if exhausted."""
    if has_active_subscription(user):
        return True
    now = datetime.now(timezone.utc)
    reset = user.free_questions_reset_at
    if reset is None or reset < now:
        user.free_questions_used = 0
        user.free_questions_reset_at = now + timedelta(days=1)
    if user.free_questions_used >= FREE_DAILY_QUESTIONS:
        await message.answer(texts.FREE_LIMIT_REACHED)
        return False
    user.free_questions_used += 1
    return True
