from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import BirthData, Reading, Subscription, User


async def upsert_user(session: AsyncSession, telegram_id: int, first_name: str | None, username: str | None) -> User:
    user = await session.get(User, telegram_id)
    if user is None:
        user = User(telegram_id=telegram_id, first_name=first_name, username=username)
        session.add(user)
    else:
        user.first_name = first_name
        user.username = username
    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id).options(
        selectinload(User.birth_data),
        selectinload(User.readings),
        selectinload(User.subscriptions),
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def require_user(session: AsyncSession, telegram_id: int) -> User:
    user = await get_user(session, telegram_id)
    if user is None:
        raise LookupError(f'User {telegram_id} not found')
    return user


async def set_gdpr_consent(session: AsyncSession, telegram_id: int, consent: bool = True) -> User:
    user = await require_user(session, telegram_id)
    user.gdpr_consent = consent
    user.gdpr_consent_date = datetime.now(timezone.utc) if consent else None
    await session.commit()
    await session.refresh(user)
    return user


async def save_birth_data(
    session: AsyncSession,
    telegram_id: int,
    birth_date: date,
    birth_time: time | None,
    birth_place: str,
    latitude: float,
    longitude: float,
    timezone_name: str,
    is_time_approximate: bool,
) -> BirthData:
    user = await require_user(session, telegram_id)
    if user.birth_data is None:
        birth = BirthData(
            user_id=telegram_id,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone_name,
            is_time_approximate=is_time_approximate,
        )
        session.add(birth)
    else:
        birth = user.birth_data
        birth.birth_date = birth_date
        birth.birth_time = birth_time
        birth.birth_place = birth_place
        birth.latitude = latitude
        birth.longitude = longitude
        birth.timezone = timezone_name
        birth.is_time_approximate = is_time_approximate
    await session.commit()
    await session.refresh(birth)
    return birth


async def create_reading(
    session: AsyncSession,
    telegram_id: int,
    reading_type: str,
    ai_response: str,
    question: str | None = None,
) -> Reading:
    reading = Reading(user_id=telegram_id, reading_type=reading_type, ai_response=ai_response, question=question)
    session.add(reading)
    await session.commit()
    await session.refresh(reading)
    return reading


async def get_recent_readings(session: AsyncSession, telegram_id: int, limit: int = 10) -> list[Reading]:
    stmt = select(Reading).where(Reading.user_id == telegram_id).order_by(Reading.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars())


async def get_questions_today(session: AsyncSession, telegram_id: int) -> int:
    today = datetime.now(timezone.utc).date()
    stmt = select(func.count(Reading.id)).where(
        Reading.user_id == telegram_id,
        Reading.reading_type == 'question',
        func.date(Reading.created_at) == today,
    )
    result = await session.execute(stmt)
    return int(result.scalar_one())


async def create_subscription(session: AsyncSession, telegram_id: int, plan_type: str, stars_amount: int) -> Subscription:
    user = await require_user(session, telegram_id)
    started_at = datetime.now(timezone.utc)
    expires_at = started_at + timedelta(days=30)
    subscription = Subscription(user_id=telegram_id, plan_type=plan_type, stars_amount=stars_amount, expires_at=expires_at)
    session.add(subscription)
    user.subscription_type = plan_type
    user.subscription_expires_at = expires_at
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def is_premium(session: AsyncSession, telegram_id: int) -> bool:
    user = await get_user(session, telegram_id)
    if user is None or user.subscription_type == 'free' or user.subscription_expires_at is None:
        return False
    return user.subscription_expires_at >= datetime.now(timezone.utc)


async def export_user_bundle(session: AsyncSession, telegram_id: int) -> dict[str, Any]:
    user = await require_user(session, telegram_id)
    readings = await get_recent_readings(session, telegram_id, limit=100)
    data = {
        'user': {
            'telegram_id': user.telegram_id,
            'first_name': user.first_name,
            'username': user.username,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'subscription_type': user.subscription_type,
            'subscription_expires_at': user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            'gdpr_consent': user.gdpr_consent,
            'gdpr_consent_date': user.gdpr_consent_date.isoformat() if user.gdpr_consent_date else None,
        },
        'birth_data': None,
        'readings': [
            {
                'id': reading.id,
                'type': reading.reading_type,
                'question': reading.question,
                'response': reading.ai_response,
                'created_at': reading.created_at.isoformat() if reading.created_at else None,
            }
            for reading in readings
        ],
        'subscriptions': [
            {
                'id': subscription.id,
                'plan_type': subscription.plan_type,
                'stars_amount': subscription.stars_amount,
                'started_at': subscription.started_at.isoformat() if subscription.started_at else None,
                'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                'status': subscription.status,
            }
            for subscription in user.subscriptions
        ],
    }
    if user.birth_data is not None:
        birth = user.birth_data
        data['birth_data'] = {
            'birth_date': birth.birth_date.isoformat(),
            'birth_time': birth.birth_time.isoformat() if birth.birth_time else None,
            'birth_place': birth.birth_place,
            'latitude': float(birth.latitude) if birth.latitude is not None else None,
            'longitude': float(birth.longitude) if birth.longitude is not None else None,
            'timezone': birth.timezone,
            'is_time_approximate': birth.is_time_approximate,
            'created_at': birth.created_at.isoformat() if birth.created_at else None,
        }
    return data


async def delete_user_data(session: AsyncSession, telegram_id: int) -> None:
    await session.execute(delete(User).where(User.telegram_id == telegram_id))
    await session.commit()
