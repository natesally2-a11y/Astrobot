"""High-level data access helpers used by the bot and the Mini App."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    BirthData,
    Reading,
    Subscription,
    SubscriptionTier,
    User,
)


# ---------- Users ----------

async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    *,
    first_name: Optional[str] = None,
    username: Optional[str] = None,
    language_code: Optional[str] = None,
    referrer_id: Optional[int] = None,
) -> User:
    user = await session.get(User, telegram_id)
    if user is None:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            language_code=language_code or "ru",
            referrer_id=referrer_id,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        changed = False
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if username and user.username != username:
            user.username = username
            changed = True
        if changed:
            await session.commit()
    return user


async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    return await session.get(User, telegram_id)


async def set_gdpr_consent(session: AsyncSession, telegram_id: int) -> None:
    user = await session.get(User, telegram_id)
    if user is None:
        return
    user.gdpr_consent = True
    user.gdpr_consent_date = datetime.now(timezone.utc)
    await session.commit()


async def delete_user(session: AsyncSession, telegram_id: int) -> None:
    await session.execute(delete(User).where(User.telegram_id == telegram_id))
    await session.commit()


# ---------- Birth data ----------

async def upsert_birth_data(
    session: AsyncSession,
    telegram_id: int,
    *,
    birth_date: date,
    birth_time: Optional[time],
    birth_place: str,
    latitude: Optional[float],
    longitude: Optional[float],
    tz_name: Optional[str],
) -> BirthData:
    existing = await session.get(BirthData, telegram_id)
    if existing is None:
        existing = BirthData(user_id=telegram_id)
        session.add(existing)
    existing.birth_date = birth_date
    existing.birth_time = birth_time
    existing.birth_place = birth_place
    existing.latitude = Decimal(str(latitude)) if latitude is not None else None
    existing.longitude = Decimal(str(longitude)) if longitude is not None else None
    existing.timezone = tz_name
    await session.commit()
    await session.refresh(existing)
    return existing


async def get_birth_data(
    session: AsyncSession, telegram_id: int
) -> Optional[BirthData]:
    return await session.get(BirthData, telegram_id)


# ---------- Readings ----------

async def save_reading(
    session: AsyncSession,
    *,
    telegram_id: int,
    reading_type: str,
    question: Optional[str],
    ai_response: str,
) -> Reading:
    reading = Reading(
        user_id=telegram_id,
        reading_type=reading_type,
        question=question,
        ai_response=ai_response,
    )
    session.add(reading)
    await session.commit()
    await session.refresh(reading)
    return reading


async def count_questions_today(session: AsyncSession, telegram_id: int) -> int:
    today_start = datetime.combine(
        datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc
    )
    stmt = (
        select(func.count(Reading.id))
        .where(Reading.user_id == telegram_id)
        .where(Reading.reading_type.in_(["ask", "daily"]))
        .where(Reading.created_at >= today_start)
    )
    result = await session.execute(stmt)
    return int(result.scalar_one() or 0)


async def get_recent_readings(
    session: AsyncSession, telegram_id: int, limit: int = 10
) -> list[Reading]:
    stmt = (
        select(Reading)
        .where(Reading.user_id == telegram_id)
        .order_by(Reading.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ---------- Subscriptions ----------

async def activate_subscription(
    session: AsyncSession,
    *,
    telegram_id: int,
    plan_type: str,
    stars_amount: int,
    telegram_payment_charge_id: Optional[str],
    days: int = 30,
) -> Subscription:
    user = await session.get(User, telegram_id)
    if user is None:
        raise ValueError(f"User {telegram_id} not found")

    now = datetime.now(timezone.utc)
    starts_from = (
        user.subscription_expires_at
        if user.subscription_expires_at and user.subscription_expires_at > now
        else now
    )
    expires_at = starts_from + timedelta(days=days)

    user.subscription_type = plan_type
    user.subscription_expires_at = expires_at

    sub = Subscription(
        user_id=telegram_id,
        plan_type=plan_type,
        stars_amount=stars_amount,
        telegram_payment_charge_id=telegram_payment_charge_id,
        expires_at=expires_at,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


async def extend_premium_days(
    session: AsyncSession, telegram_id: int, days: int
) -> None:
    """Used for referral bonuses."""
    user = await session.get(User, telegram_id)
    if user is None:
        return
    now = datetime.now(timezone.utc)
    base = (
        user.subscription_expires_at
        if user.subscription_expires_at and user.subscription_expires_at > now
        else now
    )
    user.subscription_expires_at = base + timedelta(days=days)
    if user.subscription_type == SubscriptionTier.FREE:
        user.subscription_type = SubscriptionTier.PRO
    await session.commit()
