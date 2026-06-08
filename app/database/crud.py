from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, time
from typing import Any

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BirthData, Reading, Subscription, User


async def create_or_update_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: str | None,
    username: str | None,
    referred_by: int | None = None,
) -> User:
    user = await session.get(User, telegram_id)
    if user is None:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            referred_by=referred_by,
        )
        session.add(user)
    else:
        user.first_name = first_name
        user.username = username
        if referred_by and not user.referred_by:
            user.referred_by = referred_by

    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    return await session.get(User, telegram_id)


async def get_user_with_birth_data(session: AsyncSession, telegram_id: int) -> User | None:
    query = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def upsert_birth_data(
    session: AsyncSession,
    telegram_id: int,
    birth_date: date,
    birth_time: time | None,
    birth_place: str,
    latitude: float,
    longitude: float,
    timezone: str,
    is_time_approximate: bool,
    raw_geocoding_payload: dict[str, Any] | None = None,
) -> BirthData:
    birth_data = await session.get(BirthData, telegram_id)
    if birth_data is None:
        birth_data = BirthData(
            user_id=telegram_id,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            is_time_approximate=is_time_approximate,
            raw_geocoding_payload=raw_geocoding_payload,
        )
        session.add(birth_data)
    else:
        birth_data.birth_date = birth_date
        birth_data.birth_time = birth_time
        birth_data.birth_place = birth_place
        birth_data.latitude = latitude
        birth_data.longitude = longitude
        birth_data.timezone = timezone
        birth_data.is_time_approximate = is_time_approximate
        birth_data.raw_geocoding_payload = raw_geocoding_payload

    await session.commit()
    await session.refresh(birth_data)
    return birth_data


async def set_gdpr_consent(session: AsyncSession, telegram_id: int, consent: bool) -> None:
    user = await session.get(User, telegram_id)
    if not user:
        return

    user.gdpr_consent = consent
    user.gdpr_consent_date = datetime.now(UTC).replace(tzinfo=None) if consent else None
    await session.commit()


async def create_reading(
    session: AsyncSession,
    telegram_id: int,
    reading_type: str,
    ai_response: str,
    question: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> Reading:
    reading = Reading(
        user_id=telegram_id,
        reading_type=reading_type,
        question=question,
        ai_response=ai_response,
        metadata_json=metadata_json,
    )
    session.add(reading)
    await session.commit()
    await session.refresh(reading)
    return reading


async def get_recent_readings(
    session: AsyncSession,
    telegram_id: int,
    limit: int = 10,
) -> list[Reading]:
    query = (
        select(Reading)
        .where(Reading.user_id == telegram_id)
        .order_by(desc(Reading.created_at))
        .limit(limit)
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def count_daily_questions(session: AsyncSession, telegram_id: int) -> int:
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    query = select(func.count(Reading.id)).where(
        Reading.user_id == telegram_id,
        Reading.reading_type == "ask",
        Reading.created_at >= datetime.combine(today, time.min),
        Reading.created_at < datetime.combine(tomorrow, time.min),
    )
    result = await session.execute(query)
    return int(result.scalar_one())


async def add_subscription(
    session: AsyncSession,
    telegram_id: int,
    plan_type: str,
    stars_amount: int,
    months: int = 1,
    telegram_payment_charge_id: str | None = None,
    provider_payment_charge_id: str | None = None,
) -> Subscription:
    now = datetime.utcnow()
    expires_at = now + timedelta(days=30 * months)

    subscription = Subscription(
        user_id=telegram_id,
        plan_type=plan_type,
        stars_amount=stars_amount,
        expires_at=expires_at,
        telegram_payment_charge_id=telegram_payment_charge_id,
        provider_payment_charge_id=provider_payment_charge_id,
    )
    session.add(subscription)

    user = await session.get(User, telegram_id)
    if user:
        user.subscription_type = plan_type
        user.subscription_expires_at = expires_at

    await session.commit()
    await session.refresh(subscription)
    return subscription


async def get_active_subscription(session: AsyncSession, telegram_id: int) -> Subscription | None:
    query = (
        select(Subscription)
        .where(
            Subscription.user_id == telegram_id,
            Subscription.expires_at > datetime.utcnow(),
        )
        .order_by(desc(Subscription.expires_at))
        .limit(1)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def export_user_bundle(session: AsyncSession, telegram_id: int) -> dict[str, Any]:
    user = await session.get(User, telegram_id)
    if user is None:
        return {}

    birth_data = await session.get(BirthData, telegram_id)
    readings = await get_recent_readings(session, telegram_id, limit=100)
    subscriptions_query = (
        select(Subscription)
        .where(Subscription.user_id == telegram_id)
        .order_by(desc(Subscription.started_at))
    )
    subscriptions_result = await session.execute(subscriptions_query)
    subscriptions = list(subscriptions_result.scalars().all())

    return {
        "user": {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "created_at": user.created_at.isoformat(),
            "subscription_type": user.subscription_type,
            "subscription_expires_at": (
                user.subscription_expires_at.isoformat()
                if user.subscription_expires_at
                else None
            ),
            "gdpr_consent": user.gdpr_consent,
            "gdpr_consent_date": (
                user.gdpr_consent_date.isoformat() if user.gdpr_consent_date else None
            ),
        },
        "birth_data": (
            {
                "birth_date": birth_data.birth_date.isoformat(),
                "birth_time": (
                    birth_data.birth_time.isoformat() if birth_data.birth_time else None
                ),
                "birth_place": birth_data.birth_place,
                "latitude": birth_data.latitude,
                "longitude": birth_data.longitude,
                "timezone": birth_data.timezone,
                "is_time_approximate": birth_data.is_time_approximate,
            }
            if birth_data
            else None
        ),
        "readings": [
            {
                "id": reading.id,
                "reading_type": reading.reading_type,
                "question": reading.question,
                "ai_response": reading.ai_response,
                "created_at": reading.created_at.isoformat(),
            }
            for reading in readings
        ],
        "subscriptions": [
            {
                "id": subscription.id,
                "plan_type": subscription.plan_type,
                "stars_amount": subscription.stars_amount,
                "started_at": subscription.started_at.isoformat(),
                "expires_at": subscription.expires_at.isoformat(),
                "auto_renew": subscription.auto_renew,
            }
            for subscription in subscriptions
        ],
    }


async def delete_user_data(session: AsyncSession, telegram_id: int) -> None:
    user = await session.get(User, telegram_id)
    if not user:
        return

    await session.delete(user)
    await session.commit()


async def init_models() -> None:
    from app.database.models import Base
    from app.database.session import engine

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
