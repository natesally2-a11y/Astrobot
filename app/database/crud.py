from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.models import BirthData, Reading, Subscription, User

settings = get_settings()


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    return await session.get(User, telegram_id)


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: str | None,
    username: str | None,
) -> User:
    user = await session.get(User, telegram_id)
    if user:
        user.first_name = first_name
        user.username = username
        await session.commit()
        await session.refresh(user)
        return user

    user = User(telegram_id=telegram_id, first_name=first_name, username=username)
    session.add(user)
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
    timezone: str | None,
) -> BirthData:
    model = await session.get(BirthData, user_id)
    if model is None:
        model = BirthData(
            user_id=user_id,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        )
        session.add(model)
    else:
        model.birth_date = birth_date
        model.birth_time = birth_time
        model.birth_place = birth_place
        model.latitude = latitude
        model.longitude = longitude
        model.timezone = timezone
    await session.commit()
    await session.refresh(model)
    return model


async def set_gdpr_consent(session: AsyncSession, user_id: int, consent: bool) -> None:
    user = await session.get(User, user_id)
    if user is None:
        return
    user.gdpr_consent = consent
    user.gdpr_consent_date = datetime.utcnow() if consent else None
    await session.commit()


async def add_reading(
    session: AsyncSession,
    user_id: int,
    reading_type: str,
    ai_response: str,
    question: str | None = None,
) -> Reading:
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


async def get_user_full_profile(session: AsyncSession, user_id: int) -> tuple[User | None, BirthData | None]:
    user = await session.get(User, user_id)
    birth_data = await session.get(BirthData, user_id)
    return user, birth_data


async def get_recent_readings(session: AsyncSession, user_id: int, limit: int = 20) -> list[Reading]:
    query = (
        select(Reading)
        .where(Reading.user_id == user_id)
        .order_by(Reading.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(query)
    return list(result.scalars())


def _subscription_active(user: User) -> bool:
    return user.subscription_type in {"pro", "oracle"} and bool(
        user.subscription_expires_at and user.subscription_expires_at > datetime.utcnow()
    )


async def can_ask_question(session: AsyncSession, user_id: int) -> tuple[bool, int]:
    user = await session.get(User, user_id)
    if user is None:
        return False, settings.free_daily_questions

    if _subscription_active(user):
        return True, 9999

    today = date.today()
    if user.daily_questions_date != today:
        user.daily_questions_date = today
        user.daily_questions_used = 0
        await session.commit()

    remaining = max(settings.free_daily_questions - user.daily_questions_used, 0)
    return remaining > 0, remaining


async def consume_question(session: AsyncSession, user_id: int) -> None:
    user = await session.get(User, user_id)
    if user is None:
        return
    if _subscription_active(user):
        return

    today = date.today()
    if user.daily_questions_date != today:
        user.daily_questions_date = today
        user.daily_questions_used = 0
    user.daily_questions_used += 1
    await session.commit()


async def activate_subscription(
    session: AsyncSession,
    user_id: int,
    plan_type: str,
    stars_amount: int,
    months: int = 1,
) -> Subscription | None:
    user = await session.get(User, user_id)
    if user is None:
        return None

    current_expiry = user.subscription_expires_at if user.subscription_expires_at else datetime.utcnow()
    start_from = max(current_expiry, datetime.utcnow())
    expiry = start_from + timedelta(days=30 * months)

    user.subscription_type = plan_type
    user.subscription_expires_at = expiry

    sub = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        stars_amount=stars_amount,
        expires_at=expiry,
        auto_renew=True,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


async def export_user_data(session: AsyncSession, user_id: int) -> dict:
    user, birth_data = await get_user_full_profile(session, user_id)
    readings = await get_recent_readings(session, user_id, limit=200)
    if user is None:
        return {}
    return {
        "user": {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "subscription_type": user.subscription_type,
            "subscription_expires_at": (
                user.subscription_expires_at.isoformat() if user.subscription_expires_at else None
            ),
            "gdpr_consent": user.gdpr_consent,
            "gdpr_consent_date": user.gdpr_consent_date.isoformat() if user.gdpr_consent_date else None,
        },
        "birth_data": {
            "birth_date": birth_data.birth_date.isoformat() if birth_data else None,
            "birth_time": birth_data.birth_time.isoformat() if birth_data and birth_data.birth_time else None,
            "birth_place": birth_data.birth_place if birth_data else None,
            "latitude": birth_data.latitude if birth_data else None,
            "longitude": birth_data.longitude if birth_data else None,
            "timezone": birth_data.timezone if birth_data else None,
        },
        "readings": [
            {
                "id": r.id,
                "reading_type": r.reading_type,
                "question": r.question,
                "ai_response": r.ai_response,
                "created_at": r.created_at.isoformat(),
            }
            for r in readings
        ],
    }


async def delete_user_data(session: AsyncSession, user_id: int) -> bool:
    user = await session.get(User, user_id)
    if not user:
        return False
    await session.delete(user)
    await session.commit()
    return True
