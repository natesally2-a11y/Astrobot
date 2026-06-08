"""Database CRUD operations."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    PLAN_FREE,
    BirthData,
    Reading,
    Subscription,
    User,
)

# ----------------------------------------------------------------------------
# Users
# ----------------------------------------------------------------------------


async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(selectinload(User.birth_data))
    )
    return result.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: Optional[str] = None,
    username: Optional[str] = None,
    language_code: Optional[str] = None,
    referred_by: Optional[int] = None,
) -> User:
    user = await get_user(session, telegram_id)
    if user is None:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            language_code=language_code or "ru",
            referred_by=referred_by,
        )
        session.add(user)
        await session.flush()
    else:
        # Keep profile fields fresh.
        if first_name:
            user.first_name = first_name
        if username is not None:
            user.username = username
    return user


async def set_gdpr_consent(session: AsyncSession, telegram_id: int, consent: bool) -> None:
    user = await get_user(session, telegram_id)
    if user:
        user.gdpr_consent = consent
        user.gdpr_consent_date = dt.datetime.now(dt.timezone.utc) if consent else None


# ----------------------------------------------------------------------------
# Birth data
# ----------------------------------------------------------------------------


async def upsert_birth_data(
    session: AsyncSession,
    user_id: int,
    *,
    birth_date: dt.date,
    birth_time: Optional[dt.time],
    time_known: bool,
    birth_place: str,
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str],
) -> BirthData:
    result = await session.execute(select(BirthData).where(BirthData.user_id == user_id))
    bd = result.scalar_one_or_none()
    if bd is None:
        bd = BirthData(user_id=user_id)
        session.add(bd)
    bd.birth_date = birth_date
    bd.birth_time = birth_time
    bd.time_known = time_known
    bd.birth_place = birth_place
    bd.latitude = latitude
    bd.longitude = longitude
    bd.timezone = timezone
    await session.flush()
    return bd


async def get_birth_data(session: AsyncSession, user_id: int) -> Optional[BirthData]:
    result = await session.execute(select(BirthData).where(BirthData.user_id == user_id))
    return result.scalar_one_or_none()


# ----------------------------------------------------------------------------
# Readings
# ----------------------------------------------------------------------------


async def save_reading(
    session: AsyncSession,
    user_id: int,
    reading_type: str,
    ai_response: str,
    question: Optional[str] = None,
) -> Reading:
    reading = Reading(
        user_id=user_id,
        reading_type=reading_type,
        question=question,
        ai_response=ai_response,
    )
    session.add(reading)
    await session.flush()
    return reading


async def get_recent_readings(session: AsyncSession, user_id: int, limit: int = 10):
    result = await session.execute(
        select(Reading)
        .where(Reading.user_id == user_id)
        .order_by(Reading.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ----------------------------------------------------------------------------
# Free-tier daily question quota
# ----------------------------------------------------------------------------


async def check_and_increment_quota(
    session: AsyncSession, user: User, daily_limit: int
) -> bool:
    """Return True if a question is allowed and count it, else False.

    Premium users always pass. The counter resets every calendar day.
    """
    if user.subscription_type != PLAN_FREE:
        return True

    today = dt.date.today()
    if user.questions_quota_date != today:
        user.questions_quota_date = today
        user.questions_used_today = 0

    if user.questions_used_today >= daily_limit:
        return False

    user.questions_used_today += 1
    return True


async def remaining_questions(user: User, daily_limit: int) -> int:
    if user.subscription_type != PLAN_FREE:
        return -1  # unlimited
    today = dt.date.today()
    if user.questions_quota_date != today:
        return daily_limit
    return max(0, daily_limit - user.questions_used_today)


# ----------------------------------------------------------------------------
# Subscriptions
# ----------------------------------------------------------------------------


async def activate_subscription(
    session: AsyncSession,
    user_id: int,
    plan_type: str,
    stars_amount: int,
    duration_days: int = 30,
    charge_id: Optional[str] = None,
) -> Subscription:
    user = await get_user(session, user_id)
    now = dt.datetime.now(dt.timezone.utc)

    # Stack on top of remaining time if the user is renewing/upgrading.
    base = now
    if user and user.subscription_expires_at and user.subscription_expires_at > now:
        base = user.subscription_expires_at
    expires_at = base + dt.timedelta(days=duration_days)

    if user:
        user.subscription_type = plan_type
        user.subscription_expires_at = expires_at

    sub = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        stars_amount=stars_amount,
        expires_at=expires_at,
        telegram_payment_charge_id=charge_id,
    )
    session.add(sub)
    await session.flush()
    return sub


async def extend_premium(session: AsyncSession, user_id: int, days: int) -> None:
    """Grant bonus premium days (e.g. referral reward)."""
    from app.database.models import PLAN_PRO

    user = await get_user(session, user_id)
    if not user:
        return
    now = dt.datetime.now(dt.timezone.utc)
    base = user.subscription_expires_at if (user.subscription_expires_at and user.subscription_expires_at > now) else now
    user.subscription_expires_at = base + dt.timedelta(days=days)
    if user.subscription_type == PLAN_FREE:
        user.subscription_type = PLAN_PRO


async def downgrade_if_expired(session: AsyncSession, user: User) -> User:
    """Reset to free plan when the subscription has lapsed."""
    if user.subscription_type != PLAN_FREE and user.subscription_expires_at:
        now = dt.datetime.now(dt.timezone.utc)
        expires = user.subscription_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=dt.timezone.utc)
        if expires < now:
            user.subscription_type = PLAN_FREE
            user.subscription_expires_at = None
    return user


async def increment_referral(session: AsyncSession, referrer_id: int) -> None:
    user = await get_user(session, referrer_id)
    if user:
        user.referral_count += 1


# ----------------------------------------------------------------------------
# GDPR
# ----------------------------------------------------------------------------


async def delete_user_data(session: AsyncSession, telegram_id: int) -> None:
    """Right to be forgotten — remove all user records."""
    await session.execute(delete(Reading).where(Reading.user_id == telegram_id))
    await session.execute(delete(Subscription).where(Subscription.user_id == telegram_id))
    await session.execute(delete(BirthData).where(BirthData.user_id == telegram_id))
    await session.execute(delete(User).where(User.telegram_id == telegram_id))


async def export_user_data(session: AsyncSession, telegram_id: int) -> dict:
    """Right to data portability — return a JSON-serialisable dump."""
    user = await get_user(session, telegram_id)
    if not user:
        return {}

    bd = await get_birth_data(session, telegram_id)
    readings = await get_recent_readings(session, telegram_id, limit=1000)
    subs_result = await session.execute(
        select(Subscription).where(Subscription.user_id == telegram_id)
    )
    subscriptions = list(subs_result.scalars().all())

    def iso(value):
        return value.isoformat() if value else None

    return {
        "user": {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "language_code": user.language_code,
            "created_at": iso(user.created_at),
            "subscription_type": user.subscription_type,
            "subscription_expires_at": iso(user.subscription_expires_at),
            "gdpr_consent": user.gdpr_consent,
            "gdpr_consent_date": iso(user.gdpr_consent_date),
            "referral_count": user.referral_count,
        },
        "birth_data": None
        if not bd
        else {
            "birth_date": iso(bd.birth_date),
            "birth_time": bd.birth_time.isoformat() if bd.birth_time else None,
            "time_known": bd.time_known,
            "birth_place": bd.birth_place,
            "latitude": float(bd.latitude) if bd.latitude is not None else None,
            "longitude": float(bd.longitude) if bd.longitude is not None else None,
            "timezone": bd.timezone,
        },
        "readings": [
            {
                "type": r.reading_type,
                "question": r.question,
                "response": r.ai_response,
                "created_at": iso(r.created_at),
            }
            for r in readings
        ],
        "subscriptions": [
            {
                "plan_type": s.plan_type,
                "stars_amount": s.stars_amount,
                "started_at": iso(s.started_at),
                "expires_at": iso(s.expires_at),
            }
            for s in subscriptions
        ],
    }
