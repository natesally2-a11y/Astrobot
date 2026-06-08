from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import BirthData, Reading, Subscription, SubscriptionType, User


async def upsert_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: str | None,
    username: str | None,
    referral_source_id: int | None = None,
) -> User:
    user = await session.get(User, telegram_id)
    if user is None:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            referral_source_id=referral_source_id,
        )
        session.add(user)
    else:
        user.first_name = first_name
        user.username = username
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_with_birth_data(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id).options(selectinload(User.birth_data))
    )
    return result.scalar_one_or_none()


async def save_gdpr_consent(session: AsyncSession, telegram_id: int) -> User:
    user = await session.get(User, telegram_id)
    if user is None:
        raise ValueError("User must exist before GDPR consent can be saved.")
    user.gdpr_consent = True
    user.gdpr_consent_date = datetime.now(UTC)
    await session.commit()
    await session.refresh(user)
    return user


async def save_birth_data(
    session: AsyncSession,
    user_id: int,
    birth_date: date,
    birth_time: time | None,
    birth_place: str,
    latitude: float | None,
    longitude: float | None,
    timezone: str | None,
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
    birth_data.timezone = timezone
    await session.commit()
    await session.refresh(birth_data)
    return birth_data


async def add_reading(
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


async def count_daily_questions(session: AsyncSession, user_id: int) -> int:
    start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(func.count(Reading.id)).where(
            Reading.user_id == user_id,
            Reading.reading_type == "question",
            Reading.created_at >= start_of_day,
        )
    )
    return int(result.scalar_one())


async def activate_subscription(
    session: AsyncSession,
    user_id: int,
    plan_type: str,
    stars_amount: int,
    telegram_payment_charge_id: str | None = None,
) -> Subscription:
    expires_at = datetime.now(UTC) + timedelta(days=30)
    subscription = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        stars_amount=stars_amount,
        expires_at=expires_at,
        telegram_payment_charge_id=telegram_payment_charge_id,
    )
    session.add(subscription)

    user = await session.get(User, user_id)
    if user is not None:
        user.subscription_type = plan_type
        user.subscription_expires_at = expires_at

    await session.commit()
    await session.refresh(subscription)
    return subscription


async def delete_user_data(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(User).where(User.telegram_id == user_id))
    await session.commit()


async def export_user_data(session: AsyncSession, user_id: int) -> dict[str, Any] | None:
    result = await session.execute(
        select(User)
        .where(User.telegram_id == user_id)
        .options(selectinload(User.birth_data), selectinload(User.readings), selectinload(User.subscriptions))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    return {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "username": user.username,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "subscription_type": user.subscription_type,
        "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        "gdpr_consent": user.gdpr_consent,
        "gdpr_consent_date": user.gdpr_consent_date.isoformat() if user.gdpr_consent_date else None,
        "birth_data": _birth_data_to_dict(user.birth_data),
        "readings": [
            {
                "id": reading.id,
                "reading_type": reading.reading_type,
                "question": reading.question,
                "ai_response": reading.ai_response,
                "created_at": reading.created_at.isoformat() if reading.created_at else None,
            }
            for reading in user.readings
        ],
        "subscriptions": [
            {
                "id": subscription.id,
                "plan_type": subscription.plan_type,
                "stars_amount": subscription.stars_amount,
                "started_at": subscription.started_at.isoformat() if subscription.started_at else None,
                "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
                "auto_renew": subscription.auto_renew,
            }
            for subscription in user.subscriptions
        ],
    }


def is_paid_user(user: User | None) -> bool:
    if user is None or user.subscription_type == SubscriptionType.FREE.value:
        return False
    if user.subscription_expires_at is None:
        return False
    return user.subscription_expires_at > datetime.now(UTC)


def _birth_data_to_dict(birth_data: BirthData | None) -> dict[str, Any] | None:
    if birth_data is None:
        return None
    return {
        "birth_date": birth_data.birth_date.isoformat(),
        "birth_time": birth_data.birth_time.isoformat() if birth_data.birth_time else None,
        "birth_place": birth_data.birth_place,
        "latitude": float(birth_data.latitude) if birth_data.latitude is not None else None,
        "longitude": float(birth_data.longitude) if birth_data.longitude is not None else None,
        "timezone": birth_data.timezone,
    }
