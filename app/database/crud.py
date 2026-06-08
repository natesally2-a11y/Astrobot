from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BirthData, Reading, Subscription, User


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: Optional[str],
    username: Optional[str],
) -> User:
    user = await session.get(User, telegram_id)
    if user:
        if first_name:
            user.first_name = first_name
        if username:
            user.username = username
        await session.commit()
        await session.refresh(user)
        return user

    user = User(telegram_id=telegram_id, first_name=first_name, username=username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    return await session.get(User, telegram_id)


async def save_birth_data(
    session: AsyncSession,
    user_id: int,
    birth_date: date,
    birth_time: Optional[time],
    birth_place: str,
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str],
) -> BirthData:
    query = select(BirthData).where(BirthData.user_id == user_id)
    existing = (await session.execute(query)).scalar_one_or_none()
    if existing:
        existing.birth_date = birth_date
        existing.birth_time = birth_time
        existing.birth_place = birth_place
        existing.latitude = latitude
        existing.longitude = longitude
        existing.timezone = timezone
        await session.commit()
        await session.refresh(existing)
        return existing

    record = BirthData(
        user_id=user_id,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place=birth_place,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def set_gdpr_consent(session: AsyncSession, user_id: int, consent: bool) -> None:
    user = await session.get(User, user_id)
    if not user:
        return
    user.gdpr_consent = consent
    user.gdpr_consent_date = datetime.utcnow() if consent else None
    await session.commit()


async def create_reading(
    session: AsyncSession,
    user_id: int,
    reading_type: str,
    ai_response: str,
    question: Optional[str] = None,
    metadata_json: Optional[dict[str, Any]] = None,
) -> Reading:
    reading = Reading(
        user_id=user_id,
        reading_type=reading_type,
        question=question,
        ai_response=ai_response,
        metadata_json=metadata_json,
    )
    session.add(reading)
    await session.commit()
    await session.refresh(reading)
    return reading


async def count_daily_questions(session: AsyncSession, user_id: int, day: date) -> int:
    day_start = datetime.combine(day, time.min)
    day_end = datetime.combine(day, time.max)
    query = (
        select(func.count(Reading.id))
        .where(Reading.user_id == user_id)
        .where(Reading.reading_type == "ask")
        .where(Reading.created_at.between(day_start, day_end))
    )
    return int((await session.execute(query)).scalar_one())


async def upsert_subscription(
    session: AsyncSession,
    user_id: int,
    plan_type: str,
    stars_amount: int,
    duration_days: int = 30,
) -> Subscription:
    expires_at = datetime.utcnow() + timedelta(days=duration_days)

    user = await session.get(User, user_id)
    if user:
        user.subscription_type = plan_type
        user.subscription_expires_at = expires_at

    subscription = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        stars_amount=stars_amount,
        expires_at=expires_at,
        auto_renew=True,
    )
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def get_user_with_birth_data(session: AsyncSession, user_id: int) -> tuple[Optional[User], Optional[BirthData]]:
    user = await session.get(User, user_id)
    if not user:
        return None, None
    birth_data = (
        await session.execute(select(BirthData).where(BirthData.user_id == user_id))
    ).scalar_one_or_none()
    return user, birth_data


async def get_readings(session: AsyncSession, user_id: int, limit: int = 20) -> list[Reading]:
    query = (
        select(Reading)
        .where(Reading.user_id == user_id)
        .order_by(Reading.created_at.desc())
        .limit(limit)
    )
    return list((await session.execute(query)).scalars().all())


async def delete_user_data(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(User).where(User.telegram_id == user_id))
    await session.commit()

