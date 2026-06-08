"""CRUD helpers for Stellarium AI."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BirthData, Reading, Subscription, User


# ---------- Users ----------

async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    language_code: Optional[str] = None,
    referred_by: Optional[int] = None,
) -> tuple[User, bool]:
    """Return (user, created)."""
    user = await session.get(User, telegram_id)
    if user is not None:
        # Refresh display fields opportunistically.
        if first_name and user.first_name != first_name:
            user.first_name = first_name
        if username is not None and user.username != username:
            user.username = username
        if language_code and user.language_code != language_code:
            user.language_code = language_code
        return user, False

    user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        language_code=language_code,
        referred_by=referred_by,
    )
    session.add(user)
    await session.flush()
    return user, True


async def set_gdpr_consent(session: AsyncSession, user: User) -> None:
    user.gdpr_consent = True
    user.gdpr_consent_date = datetime.now(timezone.utc)


async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    return await session.get(User, telegram_id)


async def delete_user(session: AsyncSession, telegram_id: int) -> None:
    """Hard-delete a user and all related rows (GDPR right to be forgotten)."""
    await session.execute(delete(User).where(User.telegram_id == telegram_id))


# ---------- Birth data ----------

async def upsert_birth_data(
    session: AsyncSession,
    *,
    user_id: int,
    name: Optional[str],
    birth_date: date,
    birth_time: Optional[time],
    time_is_unknown: bool,
    birth_place: str,
    latitude: float,
    longitude: float,
    timezone_name: Optional[str],
) -> BirthData:
    existing = await session.scalar(
        select(BirthData).where(BirthData.user_id == user_id)
    )
    if existing is None:
        existing = BirthData(user_id=user_id, birth_date=birth_date, birth_place=birth_place)
        session.add(existing)

    existing.name = name
    existing.birth_date = birth_date
    existing.birth_time = birth_time
    existing.time_is_unknown = time_is_unknown
    existing.birth_place = birth_place
    existing.latitude = latitude
    existing.longitude = longitude
    existing.timezone = timezone_name
    await session.flush()
    return existing


async def get_birth_data(
    session: AsyncSession, user_id: int
) -> Optional[BirthData]:
    return await session.scalar(
        select(BirthData).where(BirthData.user_id == user_id)
    )


# ---------- Readings ----------

async def add_reading(
    session: AsyncSession,
    *,
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


async def list_readings(
    session: AsyncSession, user_id: int, limit: int = 20
) -> list[Reading]:
    rows = await session.scalars(
        select(Reading)
        .where(Reading.user_id == user_id)
        .order_by(Reading.created_at.desc())
        .limit(limit)
    )
    return list(rows)


# ---------- Subscriptions ----------

async def add_subscription(
    session: AsyncSession,
    *,
    user_id: int,
    plan_type: str,
    stars_amount: int,
    duration_days: int = 30,
    telegram_payment_charge_id: Optional[str] = None,
) -> Subscription:
    now = datetime.now(timezone.utc)
    sub = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        stars_amount=stars_amount,
        started_at=now,
        expires_at=now + timedelta(days=duration_days),
        telegram_payment_charge_id=telegram_payment_charge_id,
    )
    session.add(sub)

    user = await session.get(User, user_id)
    if user is not None:
        user.subscription_type = plan_type
        existing_expiry = user.subscription_expires_at or now
        if existing_expiry < now:
            existing_expiry = now
        user.subscription_expires_at = existing_expiry + timedelta(days=duration_days)
    await session.flush()
    return sub


async def add_referral_bonus_days(
    session: AsyncSession, user_id: int, days: int
) -> None:
    """Extend Pro subscription (or grant a fresh one) as a referral reward."""
    user = await session.get(User, user_id)
    if user is None:
        return
    now = datetime.now(timezone.utc)
    base = user.subscription_expires_at or now
    if base < now:
        base = now
    user.subscription_expires_at = base + timedelta(days=days)
    user.referral_bonus_days += days
    if user.subscription_type == "free":
        user.subscription_type = "pro"


def has_active_subscription(user: User, plan: Optional[str] = None) -> bool:
    """Check whether the user's subscription is active (and matches plan)."""
    if user.subscription_type == "free":
        return False
    if user.subscription_expires_at is None:
        return False
    if user.subscription_expires_at <= datetime.now(timezone.utc):
        return False
    if plan is None:
        return True
    if plan == "pro":
        return user.subscription_type in ("pro", "oracle")
    if plan == "oracle":
        return user.subscription_type == "oracle"
    return False
