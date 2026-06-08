from datetime import datetime, date, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.database.models import User, BirthData, Reading, Subscription
from app.config import settings


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    language_code: Optional[str] = None,
    referred_by: Optional[int] = None,
) -> tuple[User, bool]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user:
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        await session.commit()
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
    await session.commit()
    await session.refresh(user)
    return user, True


async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def update_gdpr_consent(session: AsyncSession, telegram_id: int):
    await session.execute(
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(gdpr_consent=True, gdpr_consent_date=datetime.utcnow())
    )
    await session.commit()


async def save_birth_data(
    session: AsyncSession,
    user_id: int,
    birth_date: date,
    birth_time: Optional[datetime],
    birth_place: str,
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str],
) -> BirthData:
    result = await session.execute(
        select(BirthData).where(BirthData.user_id == user_id)
    )
    existing = result.scalar_one_or_none()

    birth_time_obj = birth_time.time() if birth_time else None

    if existing:
        existing.birth_date = birth_date
        existing.birth_time = birth_time_obj
        existing.birth_place = birth_place
        existing.latitude = latitude
        existing.longitude = longitude
        existing.timezone = timezone
        await session.commit()
        return existing

    birth_data = BirthData(
        user_id=user_id,
        birth_date=birth_date,
        birth_time=birth_time_obj,
        birth_place=birth_place,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
    )
    session.add(birth_data)
    await session.commit()
    await session.refresh(birth_data)
    return birth_data


async def get_birth_data(session: AsyncSession, user_id: int) -> Optional[BirthData]:
    result = await session.execute(
        select(BirthData).where(BirthData.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def save_reading(
    session: AsyncSession,
    user_id: int,
    reading_type: str,
    question: Optional[str],
    ai_response: str,
) -> Reading:
    reading = Reading(
        user_id=user_id,
        reading_type=reading_type,
        question=question,
        ai_response=ai_response,
    )
    session.add(reading)
    await session.commit()
    return reading


async def check_and_reset_questions(session: AsyncSession, user: User) -> User:
    today = date.today()
    if user.questions_reset_date != today:
        await session.execute(
            update(User)
            .where(User.telegram_id == user.telegram_id)
            .values(questions_today=0, questions_reset_date=today)
        )
        await session.commit()
        await session.refresh(user)
    return user


async def increment_questions(session: AsyncSession, telegram_id: int):
    await session.execute(
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(questions_today=User.questions_today + 1)
    )
    await session.commit()


async def activate_subscription(
    session: AsyncSession,
    user_id: int,
    plan_type: str,
    stars_amount: int,
    payment_id: Optional[str] = None,
) -> Subscription:
    duration_days = 30

    now = datetime.utcnow()
    expires_at = now + timedelta(days=duration_days)

    await session.execute(
        update(User)
        .where(User.telegram_id == user_id)
        .values(subscription_type=plan_type, subscription_expires_at=expires_at)
    )

    subscription = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        stars_amount=stars_amount,
        payment_id=payment_id,
        expires_at=expires_at,
    )
    session.add(subscription)
    await session.commit()
    return subscription


async def add_referral_bonus(session: AsyncSession, user_id: int):
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    now = datetime.utcnow()
    bonus_days = settings.REFERRAL_BONUS_DAYS

    if user.subscription_type == "free" or not user.subscription_expires_at:
        expires_at = now + timedelta(days=bonus_days)
        plan = "pro"
    else:
        expires_at = user.subscription_expires_at + timedelta(days=bonus_days)
        plan = user.subscription_type

    await session.execute(
        update(User)
        .where(User.telegram_id == user_id)
        .values(subscription_type=plan, subscription_expires_at=expires_at)
    )
    await session.commit()


async def delete_user_data(session: AsyncSession, telegram_id: int):
    await session.execute(delete(Reading).where(Reading.user_id == telegram_id))
    await session.execute(delete(Subscription).where(Subscription.user_id == telegram_id))
    await session.execute(delete(BirthData).where(BirthData.user_id == telegram_id))
    await session.execute(delete(User).where(User.telegram_id == telegram_id))
    await session.commit()


async def get_user_readings(
    session: AsyncSession, user_id: int, limit: int = 10
) -> list[Reading]:
    result = await session.execute(
        select(Reading)
        .where(Reading.user_id == user_id)
        .order_by(Reading.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
