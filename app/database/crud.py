from datetime import datetime, date, time, timedelta
from decimal import Decimal
import json

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import User, BirthData, Reading, Subscription
from app.database.session import async_session


async def get_or_create_user(
    telegram_id: int,
    first_name: str | None = None,
    username: str | None = None,
    language_code: str | None = None,
    referrer_id: int | None = None,
) -> User:
    async with async_session() as session:
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
        return user


async def get_user(telegram_id: int) -> User | None:
    async with async_session() as session:
        return await session.get(User, telegram_id)


async def get_user_with_birth_data(telegram_id: int) -> User | None:
    async with async_session() as session:
        stmt = (
            select(User)
            .options(selectinload(User.birth_data))
            .where(User.telegram_id == telegram_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def update_user(telegram_id: int, **kwargs) -> User | None:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            await session.commit()
            await session.refresh(user)
        return user


async def set_gdpr_consent(telegram_id: int) -> User | None:
    return await update_user(
        telegram_id,
        gdpr_consent=True,
        gdpr_consent_date=datetime.utcnow(),
    )


async def save_birth_data(
    user_id: int,
    birth_date: date,
    birth_time: time | None,
    birth_place: str,
    latitude: Decimal | None = None,
    longitude: Decimal | None = None,
    timezone: str | None = None,
) -> BirthData:
    async with async_session() as session:
        stmt = select(BirthData).where(BirthData.user_id == user_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.birth_date = birth_date
            existing.birth_time = birth_time
            existing.birth_place = birth_place
            existing.latitude = latitude
            existing.longitude = longitude
            existing.timezone = timezone
        else:
            existing = BirthData(
                user_id=user_id,
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
            )
            session.add(existing)

        await session.commit()
        await session.refresh(existing)
        return existing


async def get_birth_data(user_id: int) -> BirthData | None:
    async with async_session() as session:
        stmt = select(BirthData).where(BirthData.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def save_reading(
    user_id: int,
    reading_type: str,
    ai_response: str,
    question: str | None = None,
) -> Reading:
    async with async_session() as session:
        reading = Reading(
            user_id=user_id,
            reading_type=reading_type,
            question=question,
            ai_response=ai_response,
        )
        session.add(reading)
        await session.commit()
        await session.refresh(reading)
        return reading


async def get_readings(user_id: int, limit: int = 20) -> list[Reading]:
    async with async_session() as session:
        stmt = (
            select(Reading)
            .where(Reading.user_id == user_id)
            .order_by(Reading.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def check_daily_limit(user_id: int, max_questions: int) -> tuple[bool, int]:
    """Returns (can_ask, remaining_count)."""
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return False, 0

        today = date.today()
        if user.daily_questions_reset_date != today:
            user.daily_questions_used = 0
            user.daily_questions_reset_date = today
            await session.commit()

        remaining = max_questions - user.daily_questions_used
        return remaining > 0, max(0, remaining)


async def increment_daily_questions(user_id: int):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.daily_questions_used += 1
            await session.commit()


async def create_subscription(
    user_id: int,
    plan_type: str,
    stars_amount: int,
    days: int = 30,
    telegram_charge_id: str | None = None,
) -> Subscription:
    async with async_session() as session:
        now = datetime.utcnow()
        sub = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            stars_amount=stars_amount,
            telegram_charge_id=telegram_charge_id,
            started_at=now,
            expires_at=now + timedelta(days=days),
        )
        session.add(sub)

        user = await session.get(User, user_id)
        if user:
            user.subscription_type = plan_type
            user.subscription_expires_at = sub.expires_at

        await session.commit()
        await session.refresh(sub)
        return sub


async def get_active_subscription(user_id: int) -> Subscription | None:
    async with async_session() as session:
        stmt = (
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
                Subscription.expires_at > datetime.utcnow(),
            )
            .order_by(Subscription.expires_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def check_subscription_level(user_id: int) -> str:
    """Returns 'free', 'pro', or 'oracle'."""
    user = await get_user(user_id)
    if not user:
        return "free"

    if user.subscription_expires_at and user.subscription_expires_at > datetime.utcnow():
        return user.subscription_type

    if user.subscription_type != "free":
        await update_user(user_id, subscription_type="free", subscription_expires_at=None)

    return "free"


async def delete_user_data(telegram_id: int):
    """GDPR: full data deletion."""
    async with async_session() as session:
        await session.execute(delete(Reading).where(Reading.user_id == telegram_id))
        await session.execute(delete(BirthData).where(BirthData.user_id == telegram_id))
        await session.execute(delete(Subscription).where(Subscription.user_id == telegram_id))
        await session.execute(delete(User).where(User.telegram_id == telegram_id))
        await session.commit()


async def export_user_data(telegram_id: int) -> dict:
    """GDPR: export all user data as JSON-serialisable dict."""
    async with async_session() as session:
        stmt = (
            select(User)
            .options(
                selectinload(User.birth_data),
                selectinload(User.readings),
                selectinload(User.subscriptions),
            )
            .where(User.telegram_id == telegram_id)
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return {}

        data: dict = {
            "user": {
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "username": user.username,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "subscription_type": user.subscription_type,
                "gdpr_consent": user.gdpr_consent,
                "gdpr_consent_date": (
                    user.gdpr_consent_date.isoformat() if user.gdpr_consent_date else None
                ),
            },
        }

        if user.birth_data:
            bd = user.birth_data
            data["birth_data"] = {
                "birth_date": bd.birth_date.isoformat() if bd.birth_date else None,
                "birth_time": bd.birth_time.isoformat() if bd.birth_time else None,
                "birth_place": bd.birth_place,
                "latitude": float(bd.latitude) if bd.latitude else None,
                "longitude": float(bd.longitude) if bd.longitude else None,
                "timezone": bd.timezone,
            }

        data["readings"] = [
            {
                "type": r.reading_type,
                "question": r.question,
                "response": r.ai_response,
                "date": r.created_at.isoformat() if r.created_at else None,
            }
            for r in user.readings
        ]

        data["subscriptions"] = [
            {
                "plan": s.plan_type,
                "stars": s.stars_amount,
                "started": s.started_at.isoformat() if s.started_at else None,
                "expires": s.expires_at.isoformat() if s.expires_at else None,
                "active": s.is_active,
            }
            for s in user.subscriptions
        ]

        return data


async def grant_referral_bonus(referrer_id: int, days: int = 7):
    """Add days to referrer's subscription as a bonus."""
    async with async_session() as session:
        user = await session.get(User, referrer_id)
        if not user:
            return

        now = datetime.utcnow()
        if user.subscription_type == "free":
            user.subscription_type = "pro"
            user.subscription_expires_at = now + timedelta(days=days)
        elif user.subscription_expires_at and user.subscription_expires_at > now:
            user.subscription_expires_at += timedelta(days=days)
        else:
            user.subscription_type = "pro"
            user.subscription_expires_at = now + timedelta(days=days)

        await session.commit()
