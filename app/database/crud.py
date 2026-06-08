import json
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import BirthData, Partner, Reading, Subscription, User

PLAN_HIERARCHY = {"free": 0, "pro": 1, "oracle": 2}


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: str | None = None,
    username: str | None = None,
    referrer_id: int | None = None,
) -> User:
    result = await session.execute(
        select(User).options(selectinload(User.birth_data)).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if user:
        if first_name:
            user.first_name = first_name
        if username:
            user.username = username
        return user

    user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        username=username,
        referrer_id=referrer_id if referrer_id != telegram_id else None,
    )
    session.add(user)
    await session.flush()
    return user


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User).options(selectinload(User.birth_data)).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def set_gdpr_consent(session: AsyncSession, user: User) -> None:
    user.gdpr_consent = True
    user.gdpr_consent_date = datetime.now(timezone.utc)


async def save_birth_data(
    session: AsyncSession,
    user_id: int,
    birth_date: date,
    birth_time: time | None,
    birth_place: str,
    latitude: float,
    longitude: float,
    tz_name: str,
) -> BirthData:
    result = await session.execute(select(BirthData).where(BirthData.user_id == user_id))
    existing = result.scalar_one_or_none()
    if existing:
        existing.birth_date = birth_date
        existing.birth_time = birth_time
        existing.birth_place = birth_place
        existing.latitude = Decimal(str(latitude))
        existing.longitude = Decimal(str(longitude))
        existing.timezone = tz_name
        return existing

    birth_data = BirthData(
        user_id=user_id,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place=birth_place,
        latitude=Decimal(str(latitude)),
        longitude=Decimal(str(longitude)),
        timezone=tz_name,
    )
    session.add(birth_data)
    await session.flush()
    return birth_data


async def save_reading(
    session: AsyncSession,
    user_id: int,
    reading_type: str,
    question: str | None,
    ai_response: str,
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


async def get_readings(session: AsyncSession, user_id: int, limit: int = 20) -> list[Reading]:
    result = await session.execute(
        select(Reading)
        .where(Reading.user_id == user_id)
        .order_by(Reading.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


def is_subscription_active(user: User) -> bool:
    if user.subscription_type == "free":
        return False
    if user.subscription_expires_at is None:
        return False
    expires = user.subscription_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires > datetime.now(timezone.utc)


def get_effective_plan(user: User) -> str:
    if is_subscription_active(user):
        return user.subscription_type
    return "free"


def has_plan_access(user: User, required_plan: str) -> bool:
    effective = get_effective_plan(user)
    return PLAN_HIERARCHY.get(effective, 0) >= PLAN_HIERARCHY.get(required_plan, 0)


async def reset_daily_questions_if_needed(session: AsyncSession, user: User) -> None:
    today = date.today()
    if user.daily_questions_reset != today:
        user.daily_questions_used = 0
        user.daily_questions_reset = today


async def can_ask_question(session: AsyncSession, user: User) -> bool:
    if has_plan_access(user, "pro"):
        return True
    await reset_daily_questions_if_needed(session, user)
    return user.daily_questions_used < 5


async def increment_question_count(session: AsyncSession, user: User) -> None:
    if has_plan_access(user, "pro"):
        return
    await reset_daily_questions_if_needed(session, user)
    user.daily_questions_used += 1


async def activate_subscription(
    session: AsyncSession,
    user: User,
    plan_type: str,
    stars_amount: int,
    days: int = 30,
) -> Subscription:
    now = datetime.now(timezone.utc)
    current_expires = user.subscription_expires_at
    if current_expires and current_expires.tzinfo is None:
        current_expires = current_expires.replace(tzinfo=timezone.utc)

    if is_subscription_active(user) and user.subscription_type == plan_type and current_expires:
        expires_at = current_expires + timedelta(days=days)
    else:
        expires_at = now + timedelta(days=days)

    user.subscription_type = plan_type
    user.subscription_expires_at = expires_at

    subscription = Subscription(
        user_id=user.telegram_id,
        plan_type=plan_type,
        stars_amount=stars_amount,
        expires_at=expires_at,
    )
    session.add(subscription)
    await session.flush()
    return subscription


async def apply_referral_bonus(session: AsyncSession, referrer_id: int) -> None:
    referrer = await get_user(session, referrer_id)
    if not referrer:
        return
    now = datetime.now(timezone.utc)
    if is_subscription_active(referrer) and referrer.subscription_expires_at:
        expires = referrer.subscription_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        referrer.subscription_expires_at = expires + timedelta(days=7)
    else:
        referrer.subscription_type = "pro"
        referrer.subscription_expires_at = now + timedelta(days=7)


async def get_partners(session: AsyncSession, user_id: int) -> list[Partner]:
    result = await session.execute(select(Partner).where(Partner.user_id == user_id))
    return list(result.scalars().all())


async def save_partner(
    session: AsyncSession,
    user_id: int,
    name: str,
    birth_date: date,
    birth_time: time | None,
    birth_place: str,
    latitude: float,
    longitude: float,
    tz_name: str,
) -> Partner:
    partner = Partner(
        user_id=user_id,
        name=name,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place=birth_place,
        latitude=Decimal(str(latitude)),
        longitude=Decimal(str(longitude)),
        timezone=tz_name,
    )
    session.add(partner)
    await session.flush()
    return partner


async def export_user_data(session: AsyncSession, user_id: int) -> dict:
    user = await get_user(session, user_id)
    if not user:
        return {}
    readings = await get_readings(session, user_id, limit=100)
    partners = await get_partners(session, user_id)

    return {
        "user": {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "subscription_type": user.subscription_type,
            "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            "gdpr_consent": user.gdpr_consent,
            "gdpr_consent_date": user.gdpr_consent_date.isoformat() if user.gdpr_consent_date else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "birth_data": {
            "birth_date": str(user.birth_data.birth_date),
            "birth_time": str(user.birth_data.birth_time) if user.birth_data and user.birth_data.birth_time else None,
            "birth_place": user.birth_data.birth_place if user.birth_data else None,
            "latitude": float(user.birth_data.latitude) if user.birth_data and user.birth_data.latitude else None,
            "longitude": float(user.birth_data.longitude) if user.birth_data and user.birth_data.longitude else None,
            "timezone": user.birth_data.timezone if user.birth_data else None,
        }
        if user.birth_data
        else None,
        "readings": [
            {
                "type": r.reading_type,
                "question": r.question,
                "response": r.ai_response,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in readings
        ],
        "partners": [
            {
                "name": p.name,
                "birth_date": str(p.birth_date),
                "birth_place": p.birth_place,
            }
            for p in partners
        ],
    }


async def delete_user_data(session: AsyncSession, user_id: int) -> bool:
    user = await get_user(session, user_id)
    if not user:
        return False
    await session.execute(delete(Reading).where(Reading.user_id == user_id))
    await session.execute(delete(Partner).where(Partner.user_id == user_id))
    await session.execute(delete(Subscription).where(Subscription.user_id == user_id))
    await session.execute(delete(BirthData).where(BirthData.user_id == user_id))
    await session.execute(delete(User).where(User.telegram_id == user_id))
    return True


def user_data_to_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
