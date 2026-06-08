from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import BirthData, Reading, Subscription, User


FREE_DAILY_AI_LIMIT = 5
PRO_PLAN = "pro"
ORACLE_PLAN = "oracle"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: str | None = None,
    username: str | None = None,
) -> User:
    user = await session.get(User, telegram_id)
    if user is None:
        user = User(telegram_id=telegram_id, first_name=first_name, username=username)
        session.add(user)
    else:
        user.first_name = first_name or user.first_name
        user.username = username or user.username
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_with_birth_data(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id).options(selectinload(User.birth_data))
    )
    return result.scalar_one_or_none()


async def set_gdpr_consent(session: AsyncSession, telegram_id: int, consent: bool) -> User:
    user = await session.get(User, telegram_id)
    if user is None:
        user = User(telegram_id=telegram_id)
        session.add(user)
    user.gdpr_consent = consent
    user.gdpr_consent_date = utcnow() if consent else None
    await session.commit()
    await session.refresh(user)
    return user


async def upsert_birth_data(
    session: AsyncSession,
    user_id: int,
    birth_date: date,
    birth_time: time | None,
    birth_place: str,
    latitude: float | None,
    longitude: float | None,
    timezone_name: str | None,
) -> BirthData:
    birth_data = await session.get(BirthData, user_id)
    if birth_data is None:
        birth_data = BirthData(user_id=user_id)
        session.add(birth_data)
    birth_data.birth_date = birth_date
    birth_data.birth_time = birth_time
    birth_data.birth_place = birth_place
    birth_data.latitude = latitude
    birth_data.longitude = longitude
    birth_data.timezone = timezone_name
    await session.commit()
    await session.refresh(birth_data)
    return birth_data


async def save_reading(
    session: AsyncSession,
    user_id: int,
    reading_type: str,
    ai_response: str,
    question: str | None = None,
) -> Reading:
    reading = Reading(user_id=user_id, reading_type=reading_type, question=question, ai_response=ai_response)
    session.add(reading)
    await session.commit()
    await session.refresh(reading)
    return reading


async def get_recent_readings(session: AsyncSession, user_id: int, limit: int = 10) -> list[Reading]:
    result = await session.execute(
        select(Reading)
        .where(Reading.user_id == user_id)
        .order_by(Reading.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def free_questions_used_today(session: AsyncSession, user_id: int) -> int:
    start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
    result = await session.execute(
        select(func.count(Reading.id)).where(
            Reading.user_id == user_id,
            Reading.reading_type == "ask",
            Reading.created_at >= start,
        )
    )
    return int(result.scalar_one())


def has_active_paid_subscription(user: User) -> bool:
    if user.subscription_type not in {PRO_PLAN, ORACLE_PLAN}:
        return False
    return bool(user.subscription_expires_at and user.subscription_expires_at > utcnow())


async def can_ask_ai(session: AsyncSession, user: User) -> bool:
    if has_active_paid_subscription(user):
        return True
    return await free_questions_used_today(session, user.telegram_id) < FREE_DAILY_AI_LIMIT


async def activate_subscription(
    session: AsyncSession,
    user_id: int,
    plan_type: str,
    stars_amount: int,
    days: int = 30,
) -> Subscription:
    expires_at = utcnow() + timedelta(days=days)
    subscription = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        stars_amount=stars_amount,
        expires_at=expires_at,
    )
    session.add(subscription)
    user = await session.get(User, user_id)
    if user is not None:
        user.subscription_type = plan_type
        user.subscription_expires_at = expires_at
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def export_user_data(session: AsyncSession, user_id: int) -> dict[str, Any] | None:
    result = await session.execute(
        select(User)
        .where(User.telegram_id == user_id)
        .options(selectinload(User.birth_data), selectinload(User.readings), selectinload(User.subscriptions))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    def as_iso(value: Any) -> Any:
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value

    return {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "username": user.username,
        "created_at": as_iso(user.created_at),
        "subscription_type": user.subscription_type,
        "subscription_expires_at": as_iso(user.subscription_expires_at),
        "gdpr_consent": user.gdpr_consent,
        "gdpr_consent_date": as_iso(user.gdpr_consent_date),
        "birth_data": None
        if user.birth_data is None
        else {
            "birth_date": as_iso(user.birth_data.birth_date),
            "birth_time": as_iso(user.birth_data.birth_time),
            "birth_place": user.birth_data.birth_place,
            "latitude": as_iso(user.birth_data.latitude),
            "longitude": as_iso(user.birth_data.longitude),
            "timezone": user.birth_data.timezone,
        },
        "readings": [
            {
                "id": reading.id,
                "reading_type": reading.reading_type,
                "question": reading.question,
                "ai_response": reading.ai_response,
                "created_at": as_iso(reading.created_at),
            }
            for reading in user.readings
        ],
        "subscriptions": [
            {
                "id": subscription.id,
                "plan_type": subscription.plan_type,
                "stars_amount": subscription.stars_amount,
                "started_at": as_iso(subscription.started_at),
                "expires_at": as_iso(subscription.expires_at),
                "auto_renew": subscription.auto_renew,
            }
            for subscription in user.subscriptions
        ],
    }


async def delete_user_account(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(delete(User).where(User.telegram_id == user_id))
    await session.commit()
    return bool(result.rowcount)
